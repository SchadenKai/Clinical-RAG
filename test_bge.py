from milvus_model.hybrid import BGEM3EmbeddingFunction
bge_m3_ef = BGEM3EmbeddingFunction(use_fp16=False, device="cpu")
docs = ["Hello world"]
print(bge_m3_ef(docs))
