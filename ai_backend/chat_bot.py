import pandas as pd
import numpy as np
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np
import asyncio

@dataclass
class KnowledgeEntry:
    """Class to store information about each term in the knowledge base."""
    term: str
    description: str
    type: str
    embedding: np.ndarray

class InMemoryRAG:
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize the RAG system with GCP services.
        
        Args:
            project_id: Your Google Cloud project ID
            location: The location of your Vertex AI resources
        """
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Initialize models
        self.llm = GenerativeModel("gemini-1.5-flash-001")
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            "text-multilingual-embedding-002"
        )
        
        # Initialize in-memory storage
        self.knowledge_entries: List[KnowledgeEntry] = []
        self.embedding_matrix: np.ndarray = np.empty((0, 0))

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a piece of text using Vertex AI.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding values
        """
        embeddings = self.embedding_model.get_embeddings(
            [text]
        )
        return np.array(embeddings[0].values)

    def load_knowledge_base(self, excel_path: str) -> None:
        """Load and process the knowledge base from Excel file.
        
        This function:
        1. Reads the Excel file
        2. Processes each term and generates its embedding
        3. Stores everything in memory for quick access
        
        Args:
            excel_path: Path to the Excel file containing terms and descriptions
        """
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        # Clear existing data
        self.knowledge_entries = []
        
        # Process each term and its description
        for _, row in df.iterrows():
            term = row['Proper Noun '].strip()
            description = row['Description'].strip()
            term_type = row['Type'].strip()
            
            # Create combined text for embedding to capture both term and description
            combined_text = f"{term} {description}"
            embedding = self._get_embedding(combined_text)
            
            # Create and store entry
            entry = KnowledgeEntry(
                term=term,
                description=description,
                type=term_type,
                embedding=embedding
            )
            self.knowledge_entries.append(entry)
        
        # Create embedding matrix for efficient similarity search
        self.embedding_matrix = np.vstack([
            entry.embedding for entry in self.knowledge_entries
        ])
        
        print(f"Loaded {len(self.knowledge_entries)} terms into the knowledge base")

    def _cosine_similarity(self, query_embedding: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and all stored embeddings.
        
        Args:
            query_embedding: The embedding of the query text
            
        Returns:
            Array of similarity scores
        """
        # Normalize the vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        matrix_norm = self.embedding_matrix / np.linalg.norm(self.embedding_matrix, axis=1, keepdims=True)
        
        # Calculate cosine similarity
        similarities = np.dot(matrix_norm, query_norm)
        return similarities

    def find_similar_terms(self, query: str, top_k: int = 2) -> List[Tuple[KnowledgeEntry, float]]:
        """Find the most similar terms to the query using vector similarity.
        
        Args:
            query: User's question
            top_k: Number of similar terms to return
            
        Returns:
            List of tuples containing (KnowledgeEntry, similarity_score)
        """
        # Get embedding for the query
        query_embedding = self._get_embedding(query)
        
        # Calculate similarities with all entries
        similarities = self._cosine_similarity(query_embedding)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return top-k entries and their similarity scores
        return [
            (self.knowledge_entries[idx], float(similarities[idx]))
            for idx in top_indices
        ]
    async def answer_query(self, query: str) -> str:
        """Answer user queries about technical terms using RAG in Traditional Chinese."""
        # 找出最相似的前 k 個條目
        similar_terms = self.find_similar_terms(query, top_k=2)

        # 找出符合相似度閥值的文本
        filtered_terms = [(entry, score) for entry, score in similar_terms if score >= 0.6]

        if not filtered_terms:
            return (
                "無法在知識庫中找到與您的問題直接相關的術語，請嘗試換個方式描述您的問題，例如：\n"
                "- 具體指出您想要瞭解的技術或術語？\n"
                "- 提供相關的企業內部溝通場景，例如會議、工作交接、客戶對談等。\n\n"
                "本系統專注於提供即時翻譯與專有名詞優化，若您的問題與企業內部溝通、技術詞彙翻譯、跨語言協作有關，請再試一次，我們將盡力提供最佳回答！\n\n"
                "如果您希望獲得更多資訊，請參考 [台積電 CareerHack 官方網站](https://www.tsmc.com/static/english/careers/Careerhack/index.html) 或來信詢問 (careerhack@tsmc.com)。"
            )

        context = "\n\n".join([
            f"術語: {entry.term}\n定義: {entry.description}\n相似度: {score:.3f}"
            for entry, score in filtered_terms
        ])

        # 構造 prompt，指示 LLM 以繁體中文回答
        prompt = f"""根據下列技術術語及其定義，請以繁體中文回答使用者的問題： "{query}"

    上下文：
    {context}

    請提供一個清晰且有幫助的解釋，直接回應使用者的問題。請根據提供的定義解釋，但同時以簡單易懂的方式說明，並保持技術準確性。"""
        print(f'prompt: {prompt}')
        # 使用 Gemini 生成回答
        response = self.llm.generate_content(prompt)
        return response.text


    def get_term_info(self, term: str) -> Tuple[str, float]:
        """Get information about a specific term and its closest related terms.
        
        This is useful for understanding how terms are related in the knowledge base.
        
        Args:
            term: The term to look up
            
        Returns:
            Tuple of (info_string, max_similarity)
        """
        # Find the term in our knowledge base
        found_entry = None
        for entry in self.knowledge_entries:
            if entry.term.lower() == term.lower():
                found_entry = entry
                break
        
        if found_entry is None:
            return "Term not found in knowledge base.", 0.0
        
        # Get embedding for this term
        term_embedding = found_entry.embedding
        
        # Calculate similarities with all other terms
        similarities = self._cosine_similarity(term_embedding)
        
        # Get top 3 most similar terms (excluding self)
        indices = np.argsort(similarities)[-4:][::-1]  # Get one extra to exclude self
        
        info_parts = [
            f"Term: {found_entry.term}",
            f"Type: {found_entry.type}",
            f"Description: {found_entry.description}",
            "\nRelated Terms:"
        ]
        
        for idx in indices:
            entry = self.knowledge_entries[idx]
            if entry.term != found_entry.term:  # Exclude self
                info_parts.append(
                    f"- {entry.term} (Similarity: {similarities[idx]:.3f})"
                )
        
        return "\n".join(info_parts), np.max(similarities)

# Example usage
async def main():
    # Initialize the RAG system
    project_id = "tsmccareerhack2025-icsd-grp2"
    rag = InMemoryRAG(project_id=project_id)
    
    # Load the knowledge base
    rag.load_knowledge_base("knowledge.xlsx")
    
    # Example queries
    queries = [
        # "What is ETP?",
        "DDR是什麼?",
        "Can you explain what a mask is?",
        "Tell me about translation platforms",
        "你是誰?"
    ]
    
    # Test the system
    for query in queries:
        print(f"\nQuery: {query}")
        response = await rag.answer_query(query)
        print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())