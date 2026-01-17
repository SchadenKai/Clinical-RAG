from functools import lru_cache

from langchain.embeddings import Embeddings
from pymilvus import DataType, IndexType, MilvusClient

from app.core.config import settings
from app.rag.embeddings import get_embedding


class VectorClient:
    def __init__(self, embedding_model: Embeddings):
        self._client: MilvusClient = None
        self.encoder = embedding_model

    @property
    def client(self) -> MilvusClient:
        if self._client:
            return self._client
        self._client = MilvusClient(
            uri=settings.milvus_url,
            user=settings.milvus_user,
            password=settings.milvus_password,
        )
        return self._client

    def health_check(self) -> str:
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
        )
        schema.add_field(
            field_name="source",
            datatype=DataType.VARCHAR,
            max_length=settings.text_field_max_length,
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
        stats = self.client.get_collection_stats(
            collection_name=settings.milvus_collection_name
        )
        if stats["row_count"] < 1:
            docs = [
                {
                    "text": (
                        "Neural networks require vast amounts of labeled data "
                        "to converge on an optimal solution."
                    ),
                    "category": "technology",
                    "source": "https://arxiv.org/abs/2102.0034",
                },
                {
                    "text": (
                        "The aroma of freshly baked sourdough bread filled "
                        "the small kitchen."
                    ),
                    "category": "food",
                    "source": "https://cooking.nytimes.com/recipes/sourdough-guide",
                },
                {
                    "text": (
                        "Jupiter's Great Red Spot is a giant storm that has "
                        "been raging for at least 400 years."
                    ),
                    "category": "science",
                    "source": "https://solarsystem.nasa.gov/planets/jupiter/overview",
                },
                {
                    "text": (
                        "Python is a high-level, interpreted programming language "
                        "known for its readability."
                    ),
                    "category": "technology",
                    "source": "https://docs.python.org/3/tutorial/index.html",
                },
                {
                    "text": (
                        "The ancient library of Alexandria was one of the largest "
                        "and most significant libraries of the ancient world."
                    ),
                    "category": "history",
                    "source": "https://en.wikipedia.org/wiki/Library_of_Alexandria",
                },
                {
                    "text": (
                        "Regular cardiovascular exercise improves heart health "
                        "and increases stamina."
                    ),
                    "category": "health",
                    "source": "https://www.mayoclinic.org/healthy-lifestyle/fitness",
                },
                {
                    "text": (
                        "Quantum entanglement occurs when particles become correlated "
                        "in ways that the quantum state of each particle cannot be "
                        "described independently."
                    ),
                    "category": "science",
                    "source": "https://plato.stanford.edu/entries/qt-entanglement",
                },
                {
                    "text": (
                        "The golden retriever chased the tennis ball across "
                        "the grassy park."
                    ),
                    "category": "nature",
                    "source": "https://www.akc.org/dog-breeds/golden-retriever",
                },
                {
                    "text": (
                        "Inflation rates have stabilized, prompting the central bank "
                        "to pause interest rate hikes."
                    ),
                    "category": "finance",
                    "source": "https://www.bloomberg.com/markets/economics",
                },
                {
                    "text": (
                        "Impressionist painting focuses on the accurate depiction "
                        "of light in its changing qualities."
                    ),
                    "category": "art",
                    "source": "https://www.metmuseum.org/toah/hd/impr/hd_impr.htm",
                },
                {
                    "text": (
                        "A relational database organizes data into rows and columns, "
                        "while NoSQL databases use flexible data models."
                    ),
                    "category": "technology",
                    "source": "https://aws.amazon.com/relational-database",
                },
                {
                    "text": (
                        "The dense canopy of the Amazon rainforest blocks much of the "
                        "sunlight from reaching the forest floor."
                    ),
                    "category": "nature",
                    "source": "https://www.worldwildlife.org/places/amazon",
                },
                {
                    "text": (
                        "Making a perfect espresso requires precise control over "
                        "pressure, temperature, and grind size."
                    ),
                    "category": "food",
                    "source": "https://clivecoffee.com/blogs/learn/espresso-101",
                },
                {
                    "text": (
                        "Stoicism is a philosophy of personal ethics informed by its "
                        "system of logic and its views on the natural world."
                    ),
                    "category": "philosophy",
                    "source": "https://dailystoic.com/what-is-stoicism",
                },
                {
                    "text": (
                        "Docker containers package up code and all its dependencies "
                        "so the application runs quickly and reliably."
                    ),
                    "category": "technology",
                    "source": "https://docs.docker.com/get-started/overview",
                },
                {
                    "text": (
                        "The mitochondria is often referred to as the powerhouse of "
                        "the cell because it generates ATP."
                    ),
                    "category": "science",
                    "source": "https://www.genome.gov/genetics-glossary/Mitochondria",
                },
                {
                    "text": (
                        "Strategic marketing relies on understanding the target "
                        "demographic and their pain points."
                    ),
                    "category": "business",
                    "source": "https://hbr.org/topic/marketing",
                },
                {
                    "text": (
                        "Penguins are a group of aquatic flightless birds living "
                        "almost exclusively in the Southern Hemisphere."
                    ),
                    "category": "nature",
                    "source": (
                        "https://www.nationalgeographic.com/animals/birds/facts/"
                        "penguins"
                    ),
                },
                {
                    "text": (
                        "Asynchronous programming allows a unit of work to run "
                        "separately from the main application thread."
                    ),
                    "category": "technology",
                    "source": (
                        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/"
                        "Reference/Statements/async_function"
                    ),
                },
                {
                    "text": (
                        "The tectonic plates shift slowly over millions of years, "
                        "forming mountains and causing earthquakes."
                    ),
                    "category": "science",
                    "source": "https://pubs.usgs.gov/gip/dynamic/dynamic.html",
                },
            ]
            for doc in docs:
                doc["vector"] = self.encoder.embed_query(doc["text"])

            self.client.insert(
                collection_name=settings.milvus_collection_name, data=doc
            )

        self.client.load_collection(collection_name=settings.milvus_collection_name)

        results = self.client.search(
            collection_name=settings.milvus_collection_name,
            anns_field="vector",
            data=[self.encoder.embed_query("tectonic plate")],
            limit=3,
            output_fields=["text", "metadata", "source"],
        )
        for res in results:
            print(res[0].entity.get("text"))
            print(res[0].entity.get("source"))


@lru_cache()
def get_vector_client() -> VectorClient:
    embedding = get_embedding().client
    return VectorClient(embedding)
