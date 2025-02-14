from google.cloud import aiplatform
from typing import Dict, List
from dataclasses import dataclass
from vertexai.generative_models  import  GenerativeModel 
from utils import download_transcript

@dataclass
class Summary:
    """會議總結的資料結構"""
    overview: str                # 會議概述
    main_points: List[str]       # 主要討論點
    decisions: List[str]         # 決策事項
    action_items: List[Dict]     # 待辦事項（包含負責人和期限）
    keywords: List[str]          # 關鍵詞彙
    markdown: str = ""           # 完整Markdown格式的總結（可選）

class MeetingSummarizer:
    def __init__(self, project_id: str, model_id = "gemini-1.5-pro-002", location: str = "us-central1"):
        # init ai platform
        aiplatform.init(project=project_id, location=location)
        self.model = GenerativeModel(model_id)
        
    def _create_prompt(self, transcript: str) -> str:
        """建立提示模板"""
        return f"""請根據以下會議逐字稿生成結構化總結。

            會議逐字稿：
            {transcript}

            請按照以下格式輸出（使用 ### 作為分隔符）：

            ### 會議概述
            （100字以內的總體概述）

            ### 主要討論點
            （列出3-5個要點）

            ### 決策事項
            （列出所有重要決定）

            ### 待辦事項
            （格式：項目 | 負責人 | 期限）

            ### 關鍵詞彙
            （列出重要的技術術語或專業詞彙）"""

    def _parse_response(self, response: str) -> Summary:
        """解析API回應並轉換成Summary物件"""
        sections = response.split("###")
        parsed = {}
        
        for section in sections:
            if not section.strip():
                continue
            title, *content = section.split("\n", 1)
            parsed[title.strip().lower()] = content[0].strip() if content else ""

        # 解析待辦事項
        action_items = []
        if "待辦事項" in parsed:
            for line in parsed["待辦事項"].split("\n"):
                if "|" in line:
                    task, owner, deadline = [x.strip() for x in line.split("|")]
                    action_items.append({
                        "task": task,
                        "owner": owner,
                        "deadline": deadline
                    })

        overview = parsed.get("會議概述", "")
        main_points = [x.strip() for x in parsed.get("主要討論點", "").split("\n") if x.strip()]
        decisions = [x.strip() for x in parsed.get("決策事項", "").split("\n") if x.strip()]
        action_items = action_items
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

    def summarize(self, transcript: str) -> Summary:
        """生成會議總結"""
        try:
            prompt = self._create_prompt(transcript)
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"生成總結時發生錯誤: {e}")
            raise

    def format_summary(self, summary: Summary) -> str:
        """將Summary物件轉換成Markdown格式的總結"""
        formatted = f"### 會議概述"
        formatted += f"\n{summary.overview}\n"
        formatted += f"\n### 主要討論點"
        for point in summary.main_points:
            formatted += f"\n{point}"
        formatted += f"\n\n### 決策事項"
        for decision in summary.decisions:
            formatted += f"\n{decision}"
        formatted += f"\n\n### 待辦事項"
        for item in summary.action_items:
            formatted += f"\n{item['task']} (負責人: {item['owner']}, 期限: {item['deadline']})"
        formatted += f"\n\n### 關鍵詞彙"
        for keyword in summary.keywords:
            formatted += f"\n{keyword}"
        self.all = formatted
        return formatted


def main():
    project_id="hackathon-450410"
    summarizer = MeetingSummarizer(project_id=project_id)
    bucket_name = "hackathon_c2"
    file_id = "meeting_transcript"
    download_transcript(bucket_name, file_id)
    
    with open(f"{file_id}.txt", "r", encoding="utf-8") as f:
        transcript = f.read()
    
    summary = summarizer.summarize(transcript)
    
    print(summary.markdown)

if __name__ == "__main__":
    main()