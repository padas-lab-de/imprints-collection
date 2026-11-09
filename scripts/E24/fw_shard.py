import sys,os,time,io
sys.path.insert(0,'/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24')
import pyarrow.parquet as pq, pyarrow.compute as pc, pyarrow as pa
from httpfile import HFFile
# usage: fw_shard.py repo path urlcol dumpcol tag   (dumpcol '-' = none) -> shards/<tag>_<basename>
repo,path,ucol,dcol,tag=sys.argv[1:6]
out=f"/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24/shards/{tag}_{path.replace('/','_')}"
if os.path.exists(out): sys.exit(0)
t=time.time()
f=HFFile(f"https://huggingface.co/datasets/{repo}/resolve/main/{path}")
pf=pq.ParquetFile(io.BufferedReader(f,buffer_size=1<<20))
cols=[ucol]+([dcol] if dcol!='-' else [])
parts=[]
rows=0
for i in range(pf.num_row_groups):
    tb=pf.read_row_group(i,columns=cols)
    rows+=len(tb)
    host=pc.utf8_lower(pc.struct_field(pc.extract_regex(tb[ucol],r'^[a-zA-Z]+://(?P<h>[^/:?#]+)'),'h'))
    d=tb[dcol] if dcol!='-' else pa.array(['-']*len(tb))
    parts.append(pa.table({'host':host,'dump':d}).group_by(['host','dump']).aggregate([([],'count_all')]))
t2=pa.concat_tables(parts).group_by(['host','dump']).aggregate([('count_all','sum')])
t2=t2.rename_columns(['host','dump','n'])
pq.write_table(t2,out+'.tmp'); os.rename(out+'.tmp',out)
print(tag,path,"bytes",f.bytes,"reqs",f.nreq,"rows",rows,"hosts",t2.num_rows,"sec",round(time.time()-t),flush=True)
