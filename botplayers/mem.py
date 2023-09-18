from datetime import datetime
from dataclasses import dataclass
import numpy as np
from typing import List, Dict
import faiss

from .config import DEFAULT_ENGINE
from .llm import get_text_embeddings
from .util import count_message_tokens





@dataclass
class MemUnit:
    datetime: datetime
    importance: float
    content: str
    keywords: List[str]



class LongMem:
    units: List[MemUnit]
    keywords_to_units: Dict[str, List[int]]
    units_index: faiss.IndexFlatL2
    keywords_index: faiss.IndexFlatL2

    def __init__(self, embedding_engine:str = 'text-embedding-ada-002'):
        self.units = []
        self.index = faiss.IndexFlatL2(512)
        self.embedding_engine = embedding_engine

    def add(self, units: List[MemUnit]):
        ids = [len(self.units) + i for i in range(len(units))]
        self.units += units
        embeddings = get_text_embeddings(self.embedding_engine, [unit.content for unit in units])
        self.index.add_with_ids(embeddings, np.array(ids, dtype=np.int64))



class Memory:
    engine: str = DEFAULT_ENGINE
    messages: List[dict] = []
    total_num_tokens: int = 0

    def add_message(self, message: dict):
        self.messages.append(message)
        self.total_num_tokens += count_message_tokens([message], self.engine)
        

