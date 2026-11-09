import duckdb
c=duckdb.connect('known.duckdb'); c.execute("SET memory_limit='1500MB'; SET threads=3; SET temp_directory='/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24/tmpdb'")
B='/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/'
def rd(p,src): return f"select regexp_replace(lower(trim(column0)),'^www\\.','') h, '{src}' src from read_csv('{p}',header=false,columns={{'column0':'VARCHAR'}},delim='\\t',quote='',escape='') "
c.execute("create or replace table known as "+" union all ".join([rd('seed_plain.txt','seed'),rd(B+'e22_hosts.txt','e22'),rd(B+'d29/round2_frontier_rest.txt','r2')]))
print(c.execute("select src,count(*),count(distinct h) from known group by 1").fetchall())
c.execute("create or replace table kh as select distinct h from known")
c.execute("create or replace table cc43 as select distinct regexp_replace(lower(h),'^www\\.','') h from '../research/cc43_dach_hosts.parquet'")
print(c.execute("select (select count(*) from kh),(select count(*) from cc43), (select count(*) from cc43 where h not in (select h from kh))").fetchall())
