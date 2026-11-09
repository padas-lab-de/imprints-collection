import duckdb,time
T='/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33/'
t=time.time()
c=duckdb.connect(T+'q3raw.duckdb'); c.execute("install httpfs; load httpfs; SET memory_limit='1500MB'; SET threads=4; SET temp_directory='"+T+"tmpdb'")
c.execute("create table if not exists q3raw(crawl varchar, h varchar, tld varchar, fetch_200 bigint)")
done={r[0] for r in c.execute("select distinct crawl from q3raw").fetchall()}
for cr in ['CC-MAIN-2025-13','CC-MAIN-2025-08','CC-MAIN-2025-05','CC-MAIN-2024-51','CC-MAIN-2024-46']:
    if cr in done: continue
    g=f"hf://datasets/commoncrawl/host-index-testing-v2/data/crawl={cr}/*.parquet"
    c.execute(f"""insert into q3raw select '{cr}', regexp_replace(array_to_string(list_reverse(string_split(surt_host_name,',')),'.'),'^www\\.','') h, url_host_tld, fetch_200
      from read_parquet('{g}') where url_host_tld in ('de','at','ch') and fetch_200>0""")
    print(cr,c.execute("select tld,count(*) from q3raw where crawl=? group by 1",[cr]).fetchall(),round(time.time()-t),flush=True)
