import duckdb
c=duckdb.connect(); c.execute("install httpfs; load httpfs")
p='hf://datasets/HPLT/HPLT2.0_cleaned/deu_Latn/train-00000-of-04279.parquet'
print([(r[1],r[2]) for r in c.execute(f"select * from parquet_schema('{p}')").fetchall()])
print(c.execute(f"select path_in_schema,sum(total_compressed_size),sum(num_values) from parquet_metadata('{p}') group by 1").fetchall())
