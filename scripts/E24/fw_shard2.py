import sys,os,time,io,threading,http.client,urllib.parse,urllib.request
import pyarrow.parquet as pq, pyarrow.compute as pc, pyarrow as pa
from concurrent.futures import ThreadPoolExecutor
# usage: fw_shard2.py repo path urlcol dumpcol tag [threads]  (dumpcol '-' = none)
# Reads ONLY the url (+dump) column chunks via HTTP range requests; writes shards/<tag>_<path>.
repo,path,ucol,dcol,tag=sys.argv[1:6]
NT=int(sys.argv[6]) if len(sys.argv)>6 else 24
OUT=os.environ.get("OUT", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24/shards")
out=f"{OUT}/{tag}_{path.replace('/','_')}"
if os.path.exists(out): sys.exit(0)
URL=f"https://huggingface.co/datasets/{repo}/resolve/main/{path}"
class Sess:
    def __init__(s): s.resolve(); s.local=threading.local(); s.bytes=0; s.nreq=0; s.lock=threading.Lock()
    def resolve(s):
        r=urllib.request.urlopen(urllib.request.Request(URL,method='HEAD'))
        s.url=r.geturl(); s.size=int(r.headers['Content-Length']); s.u=urllib.parse.urlparse(s.url)
    def get(s,a,b):  # inclusive-exclusive
        for t in range(6):
            try:
                c=getattr(s.local,'c',None)
                if c is None: c=s.local.c=http.client.HTTPSConnection(s.u.netloc,timeout=60)
                c.request('GET',s.u.path+('?'+s.u.query if s.u.query else ''),headers={'Range':f'bytes={a}-{b-1}'})
                r=c.getresponse(); d=r.read()
                if r.status not in (200,206): raise IOError(r.status)
                with s.lock: s.bytes+=len(d); s.nreq+=1
                return d
            except Exception as e:
                s.local.c=None
                if t==3: s.resolve()
                if t==5: raise
                time.sleep(0.5*(t+1))
class Sparse(io.RawIOBase):
    def __init__(s,size,blocks): s.size=size; s.blocks=blocks; s.pos=0
    def readable(s): return True
    def seekable(s): return True
    def tell(s): return s.pos
    def seek(s,o,w=0): s.pos={0:o,1:s.pos+o,2:s.size+o}[w]; return s.pos
    def readinto(s,b):
        n=min(len(b),s.size-s.pos)
        if n<=0: return 0
        for a,d in s.blocks:
            if a<=s.pos and s.pos+n<=a+len(d):
                b[:n]=d[s.pos-a:s.pos-a+n]; s.pos+=n; return n
        d=SESS.get(s.pos,s.pos+n); b[:n]=d; s.pos+=n; return n
t0=time.time()
S=Sess(); SESS=S
tail=S.get(max(0,S.size-8),S.size); flen=int.from_bytes(tail[:4],'little')
foot=S.get(S.size-8-flen,S.size)
md=pq.ParquetFile(Sparse(S.size,[(S.size-len(foot),foot)])).metadata
names=[md.schema.column(i).name for i in range(md.num_columns)]
want=[names.index(ucol)]+([names.index(dcol)] if dcol!='-' else [])
def work(i):
    rg=md.row_group(i); rs=[]
    for j in want:
        c=rg.column(j)
        st=c.dictionary_page_offset if c.has_dictionary_page and c.dictionary_page_offset else c.data_page_offset
        rs.append((st,st+c.total_compressed_size))
    rs.sort(); m=[list(rs[0])]
    for a,b in rs[1:]:
        if a-m[-1][1]<262144: m[-1][1]=max(m[-1][1],b)
        else: m.append([a,b])
    blocks=[(a,S.get(a,b)) for a,b in m]+[(S.size-len(foot),foot)]
    tb=pq.ParquetFile(Sparse(S.size,blocks),metadata=md).read_row_group(i,columns=[ucol]+([dcol] if dcol!='-' else []))
    host=pc.utf8_lower(pc.struct_field(pc.extract_regex(tb[ucol],r'^[a-zA-Z]+://(?P<h>[^/:?#]+)'),'h'))
    d=tb[dcol] if dcol!='-' else pa.array(['-']*len(tb))
    return pa.table({'host':host,'dump':d}).group_by(['host','dump']).aggregate([([],'count_all')]), len(tb)
with ThreadPoolExecutor(NT) as ex: res=list(ex.map(work,range(md.num_row_groups)))
t2=pa.concat_tables([r[0] for r in res]).group_by(['host','dump']).aggregate([('count_all','sum')])
t2=t2.select(['host','dump','count_all_sum']).rename_columns(['host','dump','n'])
pq.write_table(t2,out+'.tmp'); os.rename(out+'.tmp',out)
print(tag,path,"filesize",S.size,"bytes",S.bytes,"reqs",S.nreq,"rows",sum(r[1] for r in res),"hosts",t2.num_rows,"rgs",md.num_row_groups,"sec",round(time.time()-t0),flush=True)
