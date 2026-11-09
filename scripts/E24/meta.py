import duckdb
c=duckdb.connect(); c.execute("install httpfs; load httpfs")
for s in [0,1,100,180]:
    pass
import json
d=json.load(open('tree_train.json'))
fs=[x['path'] for x in d]
for p in [fs[0],fs[90],fs[-1]]:
    r=c.execute(f"select sum(num_values) filter(where path_in_schema='url'), sum(total_compressed_size) filter(where path_in_schema='url'), sum(total_compressed_size) from parquet_metadata('hf://datasets/HuggingFaceFW/fineweb-2/{p}')").fetchall()
    print(p,r)
print(c.execute(f"select * from parquet_schema('hf://datasets/HuggingFaceFW/fineweb-2/{fs[0]}')").fetchall())
