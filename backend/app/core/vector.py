from functools import lru_cache

from pymilvus import DataType, IndexType, MilvusClient

from app.core.config import settings


class VectorClient:
    def __init__(self):
        self.client: MilvusClient = None

    def get_client(self) -> MilvusClient:
        if self.client:
            return self.client
        client = MilvusClient(
            uri=settings.milvus_url,
            user=settings.milvus_user,
            password=settings.milvus_password,
        )
        self.client = client
        return client

    def health_check(self) -> str:
        client = self.get_client()
        try:
            return {
                "status_code": 200,
                "message": (
                    f"Healthy: {client.get_server_type()} "
                    f"{client.get_server_version()}"
                ),
            }
        except Exception as e:
            return {"status_code": 500, "message": f"Something went wrong: {e}"}

    def setup(self) -> None:
        client = self.get_client()
        print(
            f"[DEBUG] Health check: {client.get_server_type()}:"
            f" {client.get_server_version()}"
        )

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
            field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=settings.vector_dim
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=settings.text_field_max_length   ,
        )

        print("[INFO] Creating index params...")
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_name="vector_idx",
            index_type=IndexType.HNSW,
            metric_type="IP",
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
        self, collection_name: str | None = settings.milvus_collection_name
    ) -> None:
        try:
            client = self.get_client()
            client.use_database(db_name=settings.milvus_db_name)
            client.drop_collection(collection_name=collection_name)
        except Exception as e:
            print(
                f"[ERROR] Something went wrong during deletion: {e}"
            )


@lru_cache()
def get_vector_client() -> VectorClient:
    return VectorClient()

