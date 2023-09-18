import faiss
import numpy as np

class VectorDatabase:
    pass


class FaissDatabase(VectorDatabase):
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)

    def add(self, vectors: np.ndarray):
        self.index.add(vectors)

    def search(self, vectors: np.ndarray, k: int = 1):
        return self.index.search(vectors, k)
