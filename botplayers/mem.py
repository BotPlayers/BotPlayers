import numpy as np
from typing import List
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)


class VectorDB:
    def __init__(self, name: str, embedding_dim: int) -> None:
        self.name = name
        connections.connect(name, host="localhost", port="19530")
        if not utility.has_collection("vector_db", using=self.name):
            fields = [
                FieldSchema(name="pk", dtype=DataType.INT64,
                            is_primary=True, auto_id=True),
                FieldSchema(name="embeddings",
                            dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR,
                            max_length=500),
                FieldSchema(name="timestamp", dtype=DataType.INT64),
                FieldSchema(name="tags", dtype=DataType.VARCHAR, is_array=True,
                            max_length=20)
            ]
            schema = CollectionSchema(fields, "vector db")
            self.collection = Collection(
                "vector_db", schema, consistency_level="Strong",
                using=self.name)
            self.collection.flush()
            self.collection.create_index(
                'embeddings', {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}})
        else:
            self.collection = Collection("vector_db", using=self.name)
        self.collection.load()

    def insert(self, embeddings: np.ndarray, texts: List[str]) -> None:
        assert len(embeddings) == len(texts)
        entities = [
            {"embeddings": embedding, "text": text}
            for embedding, text in zip(embeddings, texts)
        ]
        self.collection.insert(entities)
        self.collection.flush()

    def search(self, embeddings: np.ndarray, top_k: int = 10) -> List[List[int]]:
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 128, "nlist": 4096},
        }
        res = self.collection.search(
            embeddings, "embeddings", limit=top_k, params=search_params)
        return res
