from pymilvus import DataType, IndexType, MilvusClient, Function, FunctionType, AnnSearchRequest, RRFRanker

from app.core.config import settings
from app.logger import app_logger
from app.rag.embeddings import EmbeddingService
from app.services.llm.tokenizer import TokenizerService

from ._smoke_test_docs import docs as test_docs


class VectorClient:
    def __init__(
        self, embedding_service: EmbeddingService, tokenizer_service: TokenizerService
    ):
        self._client: MilvusClient = None
        self.embedding_service = embedding_service
        self.tokenizer_service = tokenizer_service

    @property
    def client(self) -> MilvusClient:
        if self._client:
            return self._client
        if settings.milvus_token:
            self._client = MilvusClient(
                uri=settings.milvus_url, token=settings.milvus_token
            )
        else:
            self._client = MilvusClient(
                uri=settings.milvus_url,
                user=settings.milvus_user,
                password=settings.milvus_password,
            )
        return self._client

    def health_check(self) -> dict:
        client = self.client
        try:
            return {
                "status_code": 200,
                "message": (
                    f"Healthy: {client.get_server_type()} {client.get_server_version()}"
                ),
            }
        except Exception as e:
            return {"status_code": 500, "message": f"Something went wrong: {e}"}

    def setup(self) -> None:
        client = self.client
        print(
            f"[DEBUG] Health check: {client.get_server_type()}:"
            f" {client.get_server_version()}"
        )
        if settings.milvus_token == "":
            if settings.milvus_db_name not in client.list_databases():
                client.create_database(db_name=settings.milvus_db_name)
            client.use_database(settings.milvus_db_name)

        if client.has_collection(settings.milvus_collection_name):
            print("[DEBUG] Collection already exists in the database.")
            return None

        print("[INFO] Creating schema...")
        schema = client.create_schema(enable_dynamic_field=True)
        schema.add_field(
            field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True
        )
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=settings.vector_dim,
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=settings.text_field_max_length,
            enable_analyzer=True,
        )
        schema.add_field(
            field_name="sparse_vector",
            datatype=DataType.SPARSE_FLOAT_VECTOR,
        )
        schema.add_field(
            field_name="source",
            datatype=DataType.VARCHAR,
            max_length=settings.text_field_max_length,
        )

        bm25_function = Function(
            name="text_bm25_emb",
            input_field_names=["text"],
            output_field_names=["sparse_vector"],
            function_type=FunctionType.BM25,
        )
        schema.add_function(bm25_function)

        print("[INFO] Creating index params...")
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_name="vector_idx",
            index_type=IndexType.HNSW,
            metric_type="IP",
        )
        index_params.add_index(
            field_name="sparse_vector",
            index_name="sparse_idx",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
        )
        client.create_collection(
            collection_name=settings.milvus_collection_name,
            schema=schema,
            index_params=index_params,
        )

    def load_collection(self) -> None:
        try:
            self.client.load_collection(settings.milvus_collection_name)
            print(
                "[DEBUG] Load state",
                self.client.get_load_state(settings.milvus_collection_name),
            )
        except Exception as e:
            print(f"[ERROR] Something went wrong during loading: {e}")

    def delete_collection(
        self,
        collection_name: str | None = settings.milvus_collection_name,
    ) -> None:
        try:
            client = self.client
            client.use_database(db_name=settings.milvus_db_name)
            client.drop_collection(collection_name=collection_name)
        except Exception as e:
            print(f"[ERROR] Something went wrong during deletion: {e}")

    def smoke_test(self):
        app_logger.info("Doing smoke test on the vector database")
        stats = self.client.get_collection_stats(
            collection_name=settings.milvus_collection_name
        )
        if stats["row_count"] < 1:
            docs_text = [doc["text"] for doc in test_docs]
            vector_list = self.embedding_service.embed_documents(
                documents=docs_text,
                tokenizer=self.tokenizer_service,
                event_name="smoke test doc ingestion",
            ).embedding
            final_docs = []
            for i, doc in enumerate(test_docs):
                final_docs.append({"vector": vector_list[i], **doc})
            self.client.insert(
                collection_name=settings.milvus_collection_name, data=final_docs
            )

        self.client.load_collection(collection_name=settings.milvus_collection_name)

        query_text = "tectonic plate"
        dense_req = AnnSearchRequest(
            data=[
                self.embedding_service.embed_query(
                    text=query_text,
                    tokenizer=self.tokenizer_service,
                    event_name="smoke test query",
                ).embedding
            ],
            anns_field="vector",
            param={"metric_type": "IP"},
            limit=3
        )
        sparse_req = AnnSearchRequest(
            data=[query_text],
            anns_field="sparse_vector",
            param={"metric_type": "BM25"},
            limit=3
        )

        results = self.client.hybrid_search(
            collection_name=settings.milvus_collection_name,
            reqs=[dense_req, sparse_req],
            ranker=RRFRanker(),
            limit=3,
            output_fields=["text", "metadata", "source"],
        )
        for res in results:
            print(res[0].entity.get("text"))
            print(res[0].entity.get("source"))
