import duckdb,sys,time,hashlib,json
# usage: agg.py "<shard glob>" <out_hosts.parquet> <new_hosts_txt> [<tag>]
glob,outp,newtxt=sys.argv[1:4]
import os  # D47: path constants below can be overridden by env
E=os.environ.get("E", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24/")
t=time.time()
c=duckdb.connect(E+'agg_'+(sys.argv[4] if len(sys.argv)>4 else 'x')+'.duckdb')
c.execute(f"SET memory_limit='1500MB'; SET threads=4; SET temp_directory='{E}tmpdb'")
c.execute("SET preserve_insertion_order=false")
c.execute(f"create or replace view src as select regexp_replace(host,'^www\\.','') h, dump, n from read_parquet('{glob}') where host<>'' and regexp_matches(host,'^[a-z0-9._-]+$')")
NB=24
c.execute("create or replace table h(host varchar, tld varchar, n_docs bigint, n_dumps bigint, dumps varchar[])")
for b in range(NB):
    c.execute(f"""insert into h select host, regexp_extract(host,'([^.]+)$',1), sum(n)::bigint, count(*), list_sort(list(dump)) from
      (select h host, dump, sum(n) n from src where hash(h)%{NB}={b} group by 1,2) group by 1""")
    print('bucket',b,round(time.time()-t),flush=True)
c.execute(f"copy h to '{outp}' (format parquet, compression zstd)")
print('distinct hosts (www-collapsed)',c.execute("select count(*) from h").fetchone()[0],'docs',c.execute("select sum(n_docs) from h").fetchone()[0],flush=True)
print('top20 tld',c.execute("select tld,count(*) hosts,sum(n_docs) docs from h group by 1 order by 2 desc limit 20").fetchall(),flush=True)
c.execute(f"attach '{E}known.duckdb' as k (read_only)")
c.execute("create or replace table nk as select h.* from h where host not in (select h from k.kh)")
print('not known total',c.execute("select count(*) from nk").fetchone()[0],flush=True)
print('not known by DACH',c.execute("select tld in ('de','at','ch') dach,count(*),sum((host not in (select h from k.cc43))::int) not_in_cc43 from nk group by 1").fetchall(),flush=True)
print('known-overlap by DACH',c.execute("select tld in ('de','at','ch') dach,count(*) from h group by 1").fetchall(),flush=True)
print('not known top tlds',c.execute("select tld,count(*) from nk group by 1 order by 2 desc limit 15").fetchall(),flush=True)
print('not known DACH with n_docs>=2',c.execute("select count(*) from nk where tld in ('de','at','ch') and n_docs>=2").fetchone(),flush=True)
c.execute(f"copy (select host from nk order by host) to '{newtxt}' (format csv, header false)")
c.execute(f"copy (select * from nk) to '{outp.replace('.parquet','_notknown.parquet')}' (format parquet, compression zstd)")
for f in (outp,newtxt):
    print(f,hashlib.sha256(open(f,'rb').read()).hexdigest())
print('sec',round(time.time()-t))
