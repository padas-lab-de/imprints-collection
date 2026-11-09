import duckdb
O='/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E33/'
c=duckdb.connect(O+'q3raw.duckdb'); c.execute("set memory_limit='1500MB'; set threads=4; set temp_directory='"+O+"tmpdb'")
print(c.execute("select crawl,count(*),count(distinct h) from q3raw group by 1 order by 1").fetchall())
c.execute(f"copy (select h, any_value(tld) tld, count(*) n_crawls from q3raw group by 1) to '{O}q3raw_distinct.parquet' (format parquet)")
print(c.execute(f"select count(*) from '{O}q3raw_distinct.parquet'").fetchall())
