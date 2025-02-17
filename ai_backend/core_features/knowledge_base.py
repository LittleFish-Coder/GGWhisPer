import faiss
import numpy as np
import pandas as pd
import logging
import concurrent.futures
from dataclasses import dataclass
from typing import List, Tuple
from sentence_transformers import SentenceTransformer  # 使用 Hugging Face 上的 BAAI/bge-m3 模型

# -----------------------------------------------------------------------------
# Logging 設定
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 知識庫條目資料結構
# -----------------------------------------------------------------------------
@dataclass
class KnowledgeEntry:
    term: str
    description: str
    type: str
    embedding: np.ndarray

# -----------------------------------------------------------------------------
# 向量資料庫 (Vector Database) 類別
# -----------------------------------------------------------------------------
class VectorDatabase:
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        # 利用 SentenceTransformer 直接載入 Hugging Face 上的 BAAI/bge-m3 模型
        self.embedding_model = SentenceTransformer("BAAI/bge-m3")
        self.knowledge_entries: List[KnowledgeEntry] = []
        self.embedding_matrix: np.ndarray = np.empty((0, 0))
        self.normalized_embedding_matrix: np.ndarray = None 
        self.index = None  # FAISS 索引

        # Executor 用來處理阻塞的呼叫
        self.executor = concurrent.futures.ThreadPoolExecutor()

    def _get_embedding(self, text: str) -> np.ndarray:
        """利用 BAAI/bge-m3 模型取得文本的向量表示"""
        try:
            embedding = self.embedding_model.encode(text)
            return np.array(embedding)
        except Exception as e:
            logger.error("取得嵌入失敗: %s", text, exc_info=True)
            raise e

    def load_knowledge_base(self, excel_path: str) -> None:
        """
        從 Excel 載入知識庫並計算所有條目的嵌入，
        同時建立正規化後的向量矩陣與 FAISS 索引。
        """
        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.strip()  # 清除欄位名稱空白

        embeddings_list = []
        for index, row in df.iterrows():
            try:
                term = str(row['Proper Noun']).strip()
                description = str(row['Description']).strip()
                term_type = str(row['Type']).strip()
                combined_text = f"{term} {description}"
                embedding = self._get_embedding(combined_text)
                entry = KnowledgeEntry(
                    term=term,
                    description=description,
                    type=term_type,
                    embedding=embedding
                )
                self.knowledge_entries.append(entry)
                embeddings_list.append(embedding)
            except Exception as e:
                logger.warning("處理第 %d 筆資料失敗：%s", index, e, exc_info=True)
                continue

        if embeddings_list:
            self.embedding_matrix = np.vstack(embeddings_list)
            # 向量正規化，這樣內積搜尋即為 cosine similarity 搜尋
            norms = np.linalg.norm(self.embedding_matrix, axis=1, keepdims=True)
            self.normalized_embedding_matrix = self.embedding_matrix / norms

            # 建立 FAISS 索引 (利用內積)
            d = self.normalized_embedding_matrix.shape[1]
            self.index = faiss.IndexFlatIP(d)
            self.index.add(self.normalized_embedding_matrix.astype('float32'))

            logger.info("知識庫已載入，共 %d 筆條目", len(self.knowledge_entries))
        else:
            logger.error("找不到有效的知識庫條目。")
            raise ValueError("知識庫載入失敗。")

    def find_similar_terms(self, query: str, top_k: int = 3) -> List[Tuple[KnowledgeEntry, float]]:
        """
        利用 FAISS 搜尋與查詢文本最相似的知識庫條目。

        Args:
            query: 使用者查詢文本。
            top_k: 返回相似度最高的條目數。
            
        Returns:
            List of (KnowledgeEntry, similarity_score) tuples。
        """
        query_embedding = self._get_embedding(query)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = np.array([query_embedding]).astype('float32')
        
        distances, indices = self.index.search(query_embedding, top_k)
        results = []
        for idx, sim in zip(indices[0], distances[0]):
            if idx < len(self.knowledge_entries):
                results.append((self.knowledge_entries[idx], float(sim)))
        return results

    def find_all_terms_above_threshold(self, query: str, threshold: float = 0.5) -> List[Tuple[KnowledgeEntry, float]]:
        """
        找出所有與查詢文本相似度大於指定閥值的知識庫條目。
        """
        query_embedding = self._get_embedding(query)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        similarities = np.dot(self.normalized_embedding_matrix, query_embedding)
        
        results = []
        for idx, sim in enumerate(similarities):
            if sim >= threshold:
                results.append((self.knowledge_entries[idx], float(sim)))
        return results
# import faiss
# import numpy as np
# import pandas as pd
# import logging
# import concurrent.futures
# from dataclasses import dataclass
# from typing import List, Tuple
# from FlagEmbedding import BGEM3FlagModel  # 使用 FlagEmbedding 來載入 BGE-M3 模型

# # -----------------------------------------------------------------------------
# # Logging 設定
# # -----------------------------------------------------------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[logging.StreamHandler()]
# )
# logger = logging.getLogger(__name__)

# # -----------------------------------------------------------------------------
# # 知識庫條目資料結構
# # -----------------------------------------------------------------------------
# @dataclass
# class KnowledgeEntry:
#     term: str
#     description: str
#     type: str
#     dense_embedding: np.ndarray
#     lexical_weights: dict

# # -----------------------------------------------------------------------------
# # 向量資料庫 (Vector Database) 類別
# # -----------------------------------------------------------------------------
# class VectorDatabase:
#     def __init__(self, project_id: str = None, location: str = "us-central1"):
#         # 初始化 BGE-M3 模型，這裡使用 FlagEmbedding 套件
#         self.embedding_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
#         self.knowledge_entries: List[KnowledgeEntry] = []
#         self.embedding_matrix: np.ndarray = np.empty((0, 0))
#         self.normalized_embedding_matrix: np.ndarray = None 
#         self.index = None  # FAISS 索引

#         # Executor 用來處理阻塞的呼叫
#         self.executor = concurrent.futures.ThreadPoolExecutor()

#     def _get_embedding(self, text: str) -> dict:
#         """
#         利用 BGE-M3 取得文本的 dense 與 sparse 輸出，
#         回傳格式為 {'dense': dense_vector, 'lexical': lexical_weights}
#         """
#         try:
#             # 設定 max_length 可根據需求調整
#             output = self.embedding_model.encode([text],
#                                                    batch_size=1,
#                                                    max_length=8192,
#                                                    return_dense=True,
#                                                    return_sparse=True,
#                                                    return_colbert_vecs=False)
#             # output 為 dict，dense_vecs 與 lexical_weights 均為 list（取第一筆）
#             return {'dense': np.array(output['dense_vecs'][0]),
#                     'lexical': output['lexical_weights'][0]}
#         except Exception as e:
#             logger.error("取得嵌入失敗: %s", text, exc_info=True)
#             raise e

#     def load_knowledge_base(self, excel_path: str) -> None:
#         """
#         從 Excel 載入知識庫並計算所有條目的 dense 與 sparse 嵌入，
#         同時建立正規化後的 dense 向量矩陣與 FAISS 索引。
#         """
#         df = pd.read_excel(excel_path)
#         df.columns = df.columns.str.strip()  # 清除欄位名稱空白

#         dense_embeddings = []
#         for index, row in df.iterrows():
#             try:
#                 term = str(row['Proper Noun']).strip()
#                 description = str(row['Description']).strip()
#                 term_type = str(row['Type']).strip()
#                 combined_text = f"{term} {description}"
#                 emb = self._get_embedding(combined_text)
#                 entry = KnowledgeEntry(
#                     term=term,
#                     description=description,
#                     type=term_type,
#                     dense_embedding=emb['dense'],
#                     lexical_weights=emb['lexical']
#                 )
#                 self.knowledge_entries.append(entry)
#                 dense_embeddings.append(emb['dense'])
#             except Exception as e:
#                 logger.warning("處理第 %d 筆資料失敗：%s", index, e, exc_info=True)
#                 continue

#         if dense_embeddings:
#             self.embedding_matrix = np.vstack(dense_embeddings)
#             # 向量正規化（dense 向量）
#             norms = np.linalg.norm(self.embedding_matrix, axis=1, keepdims=True)
#             self.normalized_embedding_matrix = self.embedding_matrix / norms

#             # 建立 FAISS 索引 (利用內積)
#             d = self.normalized_embedding_matrix.shape[1]
#             self.index = faiss.IndexFlatIP(d)
#             self.index.add(self.normalized_embedding_matrix.astype('float32'))

#             logger.info("知識庫已載入，共 %d 筆條目", len(self.knowledge_entries))
#         else:
#             logger.error("找不到有效的知識庫條目。")
#             raise ValueError("知識庫載入失敗。")

#     def _compute_combined_similarity(self, query_dense, query_lexical, entry_dense, entry_lexical, alpha=0.7) -> float:
#         """
#         計算結合 dense 與 sparse 的相似度。
#         alpha 為 dense 分數的權重，(1 - alpha) 為 sparse 的權重。
#         """
#         # Dense 相似度（cosine similarity，假設向量已正規化）
#         dense_sim = np.dot(query_dense, entry_dense)
#         # Sparse 相似度：利用模型內建函式計算 lexical matching score
#         lexical_sim = self.embedding_model.compute_lexical_matching_score(query_lexical, entry_lexical)
#         # 結合兩者
#         return alpha * dense_sim + (1 - alpha) * lexical_sim

#     def find_similar_terms(self, query: str, top_k: int = 3, alpha: float = 0.7) -> List[Tuple[KnowledgeEntry, float]]:
#         """
#         利用 FAISS 先以 dense 向量檢索候選，再利用 dense+sparse 結合相似度對候選進行重排序。
        
#         Args:
#             query: 使用者查詢文本。
#             top_k: 返回最終結果數量。
#             alpha: dense 分數權重（0~1）。
            
#         Returns:
#             List of (KnowledgeEntry, final_similarity) tuples。
#         """
#         # 取得查詢的 dense 與 sparse 輸出
#         query_emb = self._get_embedding(query)
#         query_dense = query_emb['dense'] / np.linalg.norm(query_emb['dense'])
#         query_lexical = query_emb['lexical']

#         # 利用 FAISS 先檢索候選（以 dense 向量）
#         q_vec = np.array([query_dense]).astype('float32')
#         distances, indices = self.index.search(q_vec, top_k * 3)  # 先取多一些候選
#         candidates = []
#         for idx, dense_sim in zip(indices[0], distances[0]):
#             if idx < len(self.knowledge_entries):
#                 entry = self.knowledge_entries[idx]
#                 combined_sim = self._compute_combined_similarity(query_dense, query_lexical,
#                                                                    entry.dense_embedding / np.linalg.norm(entry.dense_embedding),
#                                                                    entry.lexical_weights, alpha=alpha)
#                 candidates.append((entry, combined_sim))
#         # 依照 combined_sim 排序並返回前 top_k
#         candidates.sort(key=lambda x: x[1], reverse=True)
#         return candidates[:top_k]

#     def find_all_terms_above_threshold(self, query: str, threshold: float = 0.5, alpha: float = 0.7) -> List[Tuple[KnowledgeEntry, float]]:
#         """
#         找出所有與查詢文本結合相似度大於指定閥值的知識庫條目。
#         """
#         query_emb = self._get_embedding(query)
#         query_dense = query_emb['dense'] / np.linalg.norm(query_emb['dense'])
#         query_lexical = query_emb['lexical']

#         results = []
#         # 遍歷所有知識庫條目，計算結合相似度
#         for entry in self.knowledge_entries:
#             entry_dense_norm = entry.dense_embedding / np.linalg.norm(entry.dense_embedding)
#             combined_sim = self._compute_combined_similarity(query_dense, query_lexical,
#                                                                entry_dense_norm, entry.lexical_weights, alpha=alpha)
#             if combined_sim >= threshold:
#                 results.append((entry, combined_sim))
#         return results
