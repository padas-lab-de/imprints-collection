import duckdb
import os  # D47: path constants below can be overridden by env
T=os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/")
R=os.environ.get("R", "/home/dinzinger/GitLab/fim/imprints-collection/.claude/worktrees/dc-lead-status-20261026/")
c=duckdb.connect(T+'E33/excl.duckdb'); c.execute("set memory_limit='1500MB'; set threads=4; set temp_directory='"+T+"E33/tmpdb'")
files={'seed':R+'seed_hosts.txt.gz','e22':T+'e22_hosts.txt','r2':T+'d29/round2_frontier_rest.txt','cc43':T+'E25/cc43_dach_new.txt',
 'p1':T+'E27/pool_p1.txt','p2':T+'E27/pool_p2.txt','p3':T+'E27/pool_p3.txt','e28p1':T+'E28/p1_other_tld.txt','e28p2':T+'E28/p2_old_dach.txt',
 'e29':T+'E29/e29_rest.txt','e30':T+'E30/e30_rest.txt','e23':T+'E23/cc_german_candidates.txt'}
c.execute("create or replace table ex(h varchar, src varchar)")
for k,p in files.items():
    c.execute(f"insert into ex select distinct regexp_replace(lower(trim(column0)),'^www\\.','') h,'{k}' from read_csv('{p}',header=false,columns={{'column0':'VARCHAR'}},delim='\\t',quote='',escape='') where trim(column0)<>''")
    print(k,c.execute("select count(*) from ex where src=?",[k]).fetchone()[0],flush=True)
c.execute("create or replace table exh as select distinct h from ex")
print('distinct',c.execute("select count(*) from exh").fetchone())
