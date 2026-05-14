"""
PetroSafe Energia - Cliente Milvus
Sprint 5 - Indexação e busca vetorial
"""

import structlog
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)

logger = structlog.get_logger()


class MilvusClient:
    """Gerencia operações no Milvus: criação de collection, inserção e busca."""

    COLLECTION_NAME = "petrosafe_documents"
    DIM = 768

    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        self._collection: Collection | None = None

    def connect(self):
        """Conecta ao Milvus e carrega a collection se já existir."""
        connections.connect("default", host=self.host, port=self.port)
        logger.info("milvus_conectado", host=self.host, port=self.port)
        if utility.has_collection(self.COLLECTION_NAME):
            self._collection = Collection(self.COLLECTION_NAME)

    def create_collection(self):
        """Cria collection e índice se não existirem."""
        if utility.has_collection(self.COLLECTION_NAME):
            self._collection = Collection(self.COLLECTION_NAME)
            logger.info("collection_existente", name=self.COLLECTION_NAME)
            return

        fields = [
            FieldSchema(name="id",        dtype=DataType.VARCHAR,      max_length=100, is_primary=True),
            FieldSchema(name="texto",     dtype=DataType.VARCHAR,      max_length=8000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.DIM),
            FieldSchema(name="dataset",   dtype=DataType.VARCHAR,      max_length=200),
            FieldSchema(name="classe",    dtype=DataType.VARCHAR,      max_length=100),
            FieldSchema(name="titulo",    dtype=DataType.VARCHAR,      max_length=500),
        ]
        schema = CollectionSchema(fields, description="PetroSafe RAG Documents")
        self._collection = Collection(name=self.COLLECTION_NAME, schema=schema)

        self._collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128},
            },
        )
        logger.info("collection_criada", name=self.COLLECTION_NAME)

    def insert(self, data: list[dict]):
        """Insere chunks com embeddings na collection."""
        rows = [
            [d["id"]        for d in data],
            [d["texto"]     for d in data],
            [d["embedding"] for d in data],
            [d["dataset"]   for d in data],
            [d["classe"]    for d in data],
            [d["titulo"]    for d in data],
        ]
        self._collection.insert(rows)
        self._collection.flush()
        logger.info("insert_concluido", total=len(data))

    def load(self):
        """Carrega collection na memória para busca."""
        self._collection.load()

    def search(self, query_embedding: list[float], top_k: int = 5):
        """Busca os top_k documentos mais similares."""
        if self._collection is None:
            self._collection = Collection(self.COLLECTION_NAME)
        self._collection.load()
        return self._collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["id", "texto", "dataset", "classe", "titulo"],
        )

    def count(self) -> int:
        """Retorna total de entidades na collection."""
        return self._collection.num_entities

    def drop_collection(self):
        """Remove a collection (use com cuidado)."""
        if utility.has_collection(self.COLLECTION_NAME):
            utility.drop_collection(self.COLLECTION_NAME)
            self._collection = None
            logger.info("collection_removida", name=self.COLLECTION_NAME)
