from pymilvus import MilvusClient, DataType, Function, FunctionType, AnnSearchRequest, RRFRanker

client = MilvusClient(uri="http://localhost:19530")
client.drop_collection("test_bm25")

schema = client.create_schema(enable_dynamic_field=True)
schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=1000, enable_analyzer=True)
schema.add_field(field_name="sparse", datatype=DataType.SPARSE_FLOAT_VECTOR)

bm25_function = Function(
    name="bm25_emb",
    input_field_names=["text"],
    output_field_names=["sparse"],
    function_type=FunctionType.BM25,
)
schema.add_function(bm25_function)

index_params = client.prepare_index_params()
index_params.add_index(field_name="sparse", index_name="sparse_idx", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")

client.create_collection(
    collection_name="test_bm25",
    schema=schema,
    index_params=index_params
)

client.insert("test_bm25", [
    {"text": "Artificial intelligence was founded as an academic discipline in 1956."},
    {"text": "Alan Turing was the first person to conduct substantial research in AI."},
])

client.load_collection("test_bm25")

search_params = {"metric_type": "BM25"}
req = AnnSearchRequest(data=["Alan Turing"], anns_field="sparse", param=search_params, limit=2)
res = client.hybrid_search("test_bm25", [req], ranker=RRFRanker(), limit=2, output_fields=["text"])
print(res)
