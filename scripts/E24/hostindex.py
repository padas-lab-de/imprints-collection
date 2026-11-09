import duckdb,time
t=time.time()
c=duckdb.connect('hi.duckdb'); c.execute("install httpfs; load httpfs; SET memory_limit='1500MB'; SET threads=2; SET temp_directory='/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E24/tmpdb'")
g="hf://datasets/commoncrawl/host-index-testing-v2/data/crawl=CC-MAIN-2025-18/*.parquet"
c.execute(f"""create or replace table hi as select regexp_replace(array_to_string(list_reverse(string_split(surt_host_name,',')),'.'),'^www\\.','') h, url_host_tld tld, fetch_200, fetch_200_lote_pct lote
 from read_parquet('{g}') where url_host_tld in ('de','at','ch')""")
print('loaded',time.time()-t,flush=True)
print(c.execute("select tld,count(*),count(distinct h),sum((fetch_200>0)::int),sum((fetch_200>0 and coalesce(lote,100)<=100)::int) from hi group by 1").fetchall(),flush=True)
c.execute("attach 'known.duckdb' as k (read_only)")
print(c.execute("""select tld,count(*) n200, sum((h not in (select h from k.kh))::int) notknown, sum((h not in (select h from k.kh) and h not in (select h from k.cc43))::int) notknown_notcc43 from (select distinct h,tld from hi where fetch_200>0) group by 1""").fetchall(),flush=True)
c.execute("copy (select distinct h from hi where fetch_200>0 and h not in (select h from k.kh)) to 'new_hosts_hostindex_2025-18.txt' (format csv, header false)")
print('done',time.time()-t)
