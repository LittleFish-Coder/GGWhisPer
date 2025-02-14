import asyncio
import logging
import concurrent.futures
import vertexai
from typing import Optional
from vertexai.generative_models import GenerativeModel
from knowledge_base import VectorDatabase  # 支援 BGE-M3 dense+sparse 的向量資料庫

# -----------------------------------------------------------------------------
# Logging 設定
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class Chatbot:
    def __init__(self, project_id: str, location: str = "us-central1", knowledge_file: Optional[str] = None):
        """
        初始化 Chatbot，並自動載入知識庫。
        
        Args:
            project_id: GCP 專案 ID。
            location: Vertex AI 資源區域。
            knowledge_file: 知識庫 Excel 檔案。
        """
        # 初始化 Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # 設定主要和備用 LLM 模型
        self.primary_llm = GenerativeModel("gemini-1.5-flash-002")
        self.backup_llm = GenerativeModel("gemini-1.5-flash-001")
        
        # 建立向量資料庫並載入知識庫
        self.vector_db = None
        # try:
        #     self.vector_db = VectorDatabase(project_id=project_id, location=location)
        #     self.vector_db.load_knowledge_base(knowledge_file)
        #     logger.info("知識庫載入完成！")
        # except Exception as e:
        #     logger.error("載入知識庫失敗: %s", e, exc_info=True)
        if knowledge_file:
            try:
                self.vector_db = VectorDatabase(project_id=project_id)
                self.vector_db.load_knowledge_base(knowledge_file)
                print("知識庫載入完成！")
            except Exception as e:
                print("載入知識庫失敗：", e)
                self.vector_db = None
        self.executor = concurrent.futures.ThreadPoolExecutor()
    
    # async def answer_query(self, query: str, similarity_threshold: float = 0.5) -> str:
    #     """
    #     回答使用者查詢：
    #      1. 利用向量資料庫搜尋相似的專業術語。
    #      2. 若有符合的上下文則組成提示交給 LLM 生成回答。
    #      3. 若主要 LLM 模型失敗，則嘗試使用備用模型。
    #     """
    #     try:
    #         similar_terms = self.vector_db.find_similar_terms(query, top_k=10) if self.vector_db else []
    #         filtered_terms = [(entry, score) for entry, score in similar_terms if score >= similarity_threshold]

    #         loop = asyncio.get_running_loop()
    #         if filtered_terms:
    #             context = "\n\n".join([
    #                 f"術語: {entry.term}\n定義: {entry.description}\n相似度: {score:.3f}"
    #                 for entry, score in filtered_terms
    #             ])
    #             prompt = (
    #                 f"根據下列技術術語及其定義，請以繁體中文回答使用者的問題： \"{query}\"\n\n"
    #                 f"上下文：\n{context}\n\n"
    #                 "請提供一個清晰且有幫助的解釋，直接回應使用者的問題。"
    #             )
    #         else:
    #             prompt = f"請直接根據您的知識回答下列問題： \"{query}\""

    #         # 嘗試使用主要模型
    #         try:
    #             response = await loop.run_in_executor(self.executor, self.primary_llm.generate_content, prompt)
    #             return response.text
    #         except Exception as e:
    #             logger.error("主要模型生成回答時發生錯誤：%s", e, exc_info=True)
                
    #             # 切換至備用模型
    #             try:
    #                 response = await loop.run_in_executor(self.executor, self.backup_llm.generate_content, prompt)
    #                 return response.text
    #             except Exception as e2:
    #                 logger.error("備用模型也發生錯誤：%s", e2, exc_info=True)
    #                 return "回答查詢時發生錯誤，請稍後再試。"
            
    #     except Exception as e:
    #         logger.error("回答查詢時發生錯誤", exc_info=True)
    #         return "回答查詢時發生錯誤，請稍後再試。"
    async def answer_query(self, query: str, similarity_threshold: float = 0.5) -> tuple:
        """
        回答使用者查詢：
        1. 利用向量資料庫搜尋相似的專業術語。
        2. 若有符合的上下文則組成提示交給 LLM 生成回答。
        3. 若主要 LLM 模型失敗，則嘗試使用備用模型。
        return response_text, has_related_terms
        """
        try:
            similar_terms = self.vector_db.find_similar_terms(query, top_k=10) if self.vector_db else []
            filtered_terms = [(entry, score) for entry, score in similar_terms if score >= similarity_threshold]

            instruct_prompt = f"請以淫蕩的語氣，用繁體中文回答下列問題： \n"            

            loop = asyncio.get_running_loop()
            if filtered_terms:
                context = "\n\n".join([
                    f"術語: {entry.term}\n定義: {entry.description}\n相似度: {score:.3f}"
                    for entry, score in filtered_terms
                ])
                prompt = (
                    f"根據下列技術術語及其定義，請以繁體中文回答使用者的問題： \"{query}\"\n\n"
                    f"上下文：\n{context}\n\n"
                    "請提供一個清晰且有幫助的解釋，直接回應使用者的問題。"
                )
            else:
                prompt = f"請直接根據您的知識回答下列問題： \"{query}\""

            prompt = instruct_prompt + prompt
            # 嘗試使用主要模型
            try:
                response = await loop.run_in_executor(self.executor, self.primary_llm.generate_content, prompt)
                response_text = response.text
            except Exception as e:
                logger.error("主要模型生成回答時發生錯誤：%s", e, exc_info=True)

                # 切換至備用模型
                try:
                    response = await loop.run_in_executor(self.executor, self.backup_llm.generate_content, prompt)
                    response_text = response.text
                except Exception as e2:
                    logger.error("備用模型也發生錯誤：%s", e2, exc_info=True)
                    return "回答查詢時發生錯誤，請稍後再試。", False

            # 若沒有找到相關術語，則在輸出結果後面附加額外訊息
            if not filtered_terms:
                # response_text += (
                #     "\n\n無法在知識庫中找到與您的問題直接相關的術語，請嘗試換個方式描述您的問題，例如：\n"
                #     "- 具體指出您想要瞭解的技術或術語？\n"
                #     "- 提供相關的企業內部溝通場景，例如會議、工作交接、客戶對談等。\n\n"
                #     "本系統專注於提供即時翻譯與專有名詞優化，若您的問題與企業內部溝通、技術詞彙翻譯、跨語言協作有關，請再試一次，我們將盡力提供最佳回答！\n\n"
                #     "如果您希望獲得更多資訊，請參考 [台積電 CareerHack 官方網站](https://www.tsmc.com/static/english/careers/Careerhack/index.html) 或來信詢問 (careerhack@tsmc.com)。"
                # )
                return response_text, False
            
            return response_text, True

        except Exception as e:
            logger.error("回答查詢時發生錯誤", exc_info=True)
            return "回答查詢時發生錯誤，請稍後再試。", False

async def main():
    project_id = "hackathon-450410"
    chatbot = Chatbot(project_id=project_id,knowledge_file="knowledge.xlsx")
    
    while True:
        query = input("請輸入查詢（輸入 exit 離開）：")
        if query.strip().lower() == "exit":
            break

        response = await chatbot.answer_query(query)
        logger.info("回答: %s", response)

if __name__ == "__main__":
    asyncio.run(main())
