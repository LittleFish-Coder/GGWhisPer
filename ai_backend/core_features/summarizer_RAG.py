
from google.cloud import aiplatform
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from vertexai.generative_models import GenerativeModel
from utils import download_transcript
from knowledge_base import VectorDatabase  # 使用我們修改後支援 BGE-M3 dense+sparse 的向量資料庫

# =============================================================================
# 會議總結資料結構
# =============================================================================
@dataclass
class Summary:
    """會議總結的資料結構"""
    overview: str                # 會議概述
    main_points: List[str]       # 主要討論點
    decisions: List[str]         # 決策事項
    action_items: List[Dict]     # 待辦事項（包含負責人和期限）
    keywords: List[str]          # 關鍵詞彙
    markdown: str = ""           # 完整 Markdown 格式的總結（可選）

# =============================================================================
# 會議總結生成器，利用向量資料庫提供上下文資訊
# =============================================================================
class MeetingSummarizer:
    def __init__(self, project_id: str, model_id: str = "gemini-1.5-flash-002", 
                 location: str = "us-central1", knowledge_file: Optional[str] = None):
        """
        初始化會議總結生成器，若提供 knowledge_file 則自動建立並載入向量資料庫。
        
        Args:
            project_id: GCP 專案 ID。
            model_id: 使用的生成模型 ID。
            location: Vertex AI 的資源區域。
            knowledge_file: (選填) 知識庫檔案路徑，若有提供，則自動建立 VectorDatabase 並載入。
        """
        aiplatform.init(project=project_id, location=location)
        # 設定主要與備用 LLM 模型
        self.primary_llm = GenerativeModel("gemini-1.5-flash-002")
        self.backup_llm = GenerativeModel("gemini-1.5-flash-001")
        self.rag = None
        if knowledge_file:
            try:
                self.rag = VectorDatabase(project_id=project_id)
                self.rag.load_knowledge_base(knowledge_file)
                print("知識庫載入完成！")
            except Exception as e:
                print("載入知識庫失敗：", e)
                self.rag = None

    def _create_prompt(self, transcript: str) -> str:
        """
        建立提示模板：
          - 對逐字稿利用向量資料庫搜尋相似的專業術語（包含術語、定義、相似度）。
          - 只保留相似度大於 0.55 的結果。
          - 將查詢結果作為上下文，並讓 LLM 依此生成結構化總結。
        """
        context_str = ""
        if self.rag is not None:
            similarity_threshold = 0.5  # 設定閥值
            similar_terms: List[Tuple] = self.rag.find_similar_terms(transcript, top_k=10)
            filtered_terms = [(entry, sim) for entry, sim in similar_terms if sim >= similarity_threshold]

            if filtered_terms:
                context_lines = [
                    f"術語: {entry.term}\n定義: {entry.description}\n相似度: {sim:.3f}"
                    for entry, sim in filtered_terms
                ]
                context_str = "\n\n".join(context_lines)
            else:
                context_str = "未檢索到符合條件的專業術語。"
        else:
            context_str = "（未提供 vector database 相關上下文。）"
        print(context_str)
        
        prompt = f"""請根據以下會議逐字稿生成結構化總結。

【會議逐字稿】：
{transcript}

【上下文提示】：
以下資料是從專業術語知識庫中依據會議逐字稿搜尋得到的符合閥值的資訊，請根據這些資訊協助生成總結：
{context_str}

【請按照以下格式輸出】（使用 ### 作為分隔符）：
--------------------------------
### 會議概述
（請提供100字以內的總體概述）

### 主要討論點
（請列出3-5個主要討論點）

### 決策事項
（請列出所有重要決定）

### 待辦事項
（請依格式：項目 | 負責人 | 期限 列出待辦事項）

### 關鍵詞彙
（請根據上方上下文完整列出所有專業術語）
--------------------------------
"""
        return prompt
   
    def summarize(self, transcript: str) -> Summary:
        """生成會議總結"""
        try:
            prompt = self._create_prompt(transcript)
            # 先嘗試使用主要模型
            try:
                response = self.primary_llm.generate_content(prompt)
                return self._parse_response(response.text)
            except Exception as e:
                print(f"主要模型失敗: {e}")
                # 主要模型失敗時，切換到備用模型
                response = self.backup_llm.generate_content(prompt)
                return self._parse_response(response.text)
        except Exception as e:
            print(f"生成總結時發生錯誤: {e}")
            raise

    def _parse_response(self, response: str) -> Summary:
        """解析 API 回應並轉換成 Summary 物件"""
        sections = response.split("###")
        parsed = {}

        for section in sections:
            if not section.strip():
                continue
            title, *content = section.split("\n", 1)
            parsed[title.strip().lower()] = content[0].strip() if content else ""

        # 對於「待辦事項」部分，不強制拆分，而直接保留原始文字（字串形式）
        action_items = []
        if "待辦事項" in parsed:
            action_items = [parsed["待辦事項"]]

        overview = parsed.get("會議概述", "")
        main_points = [x.strip() for x in parsed.get("主要討論點", "").split("\n") if x.strip()]
        decisions = [x.strip() for x in parsed.get("決策事項", "").split("\n") if x.strip()]
        keywords = [x.strip() for x in parsed.get("關鍵詞彙", "").split("\n") if x.strip()]

        markdown = self.format_summary(
            Summary(overview=overview, main_points=main_points, decisions=decisions, action_items=action_items, keywords=keywords)
        )

        return Summary(
            overview=overview,
            main_points=main_points,
            decisions=decisions,
            action_items=action_items,
            keywords=keywords,
            markdown=markdown
        )

    def format_summary(self, summary: Summary) -> str:
        """將 Summary 物件轉換成 Markdown 格式的總結"""
        formatted = f"### 會議概述\n{summary.overview}\n"
        formatted += "\n### 主要討論點"
        for point in summary.main_points:
            formatted += f"\n{point}"
        formatted += "\n\n### 決策事項"
        for decision in summary.decisions:
            formatted += f"\n{decision}"
        formatted += "\n\n### 待辦事項"
        # 如果 action_items 為字串就直接輸出，否則按照 dict 處理
        for item in summary.action_items:
            if isinstance(item, dict):
                formatted += f"\n{item.get('task', '')} (負責人: {item.get('owner', '')}, 期限: {item.get('deadline', '')})"
            else:
                formatted += f"\n{item}"
        formatted += "\n\n### 關鍵詞彙"
        for keyword in summary.keywords:
            formatted += f"\n{keyword}"
        return formatted



def main():
    project_id = "hackathon-450410"
    file_id = "Training_twoStage"
    with open(f"{file_id}.txt", "r", encoding="utf-8") as f:
        transcript = f.read()
    
    # 在 new MeetingSummarizer 時直接提供 knowledge_file 以自動載入向量資料庫
    summarizer = MeetingSummarizer(project_id=project_id, knowledge_file="knowledge.xlsx")
    summary = summarizer.summarize(transcript)
    print(summary.markdown)


if __name__ == "__main__":
    main()
