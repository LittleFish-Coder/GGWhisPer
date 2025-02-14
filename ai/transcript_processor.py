import pandas as pd
import re
import vertexai
from vertexai.generative_models import GenerativeModel
import os

class TranscriptProcessor:
    def __init__(self, transcript_text, target_language, 
                 excel_path="../dataset/Training/Knowledge Dataset.xlsx",
                 project_id="hackathon-450410", location="us-central1"):
        """
        初始化：
          - transcript_text：逐字稿的文字內容（若原來有檔案路徑，可先自行讀檔）
          - target_language：目標語言 (例如 "cmn-Hant-TW"、"en-US"、"ja-JP"、"de-DE")
          - excel_path：proper noun 資料表的路徑
          - project_id 與 location：Vertex AI 初始化所需參數
        """
        self.transcript_text = transcript_text
        self.target_language = target_language
        self.excel_path = excel_path
        self.project_id = project_id
        self.location = location
        os.makedirs("results", exist_ok=True)

        # 初始化 Vertex AI 環境
        vertexai.init(project=self.project_id, location=self.location)
        # 讀取 Excel 並建立 proper_nouns_dict
        self.proper_nouns_dict = self.load_proper_nouns()
        # 定義輸出逐字稿檔案名稱
        self.output_transcript_path = f"transcript_{self.target_language}.txt"

    def load_proper_nouns(self):
        """
        讀取 Excel 並建立 proper_nouns_dict
        """
        sheets = ["cmn-Hant-TW", "en-US", "ja-JP", "de-DE"]
        # 讀取各個 sheet，並移除欄位前後空白
        dfs = {sheet: pd.read_excel(self.excel_path, sheet_name=sheet).rename(columns=lambda x: x.strip())
               for sheet in sheets}

        proper_nouns_dict = {}
        for idx in dfs["en-US"].index:
            en_proper_noun = dfs["en-US"].loc[idx, "Proper Noun"]
            if pd.notna(en_proper_noun):
                proper_nouns = {}
                for sheet in sheets:
                    pn = dfs[sheet].loc[idx, "Proper Noun"]
                    if pd.notna(pn):
                        proper_nouns[sheet] = pn.strip()    # type: ignore
                if proper_nouns:
                    proper_nouns_dict[en_proper_noun] = {
                        "Type": dfs["en-US"].loc[idx, "Type"],
                        "Proper Nouns": proper_nouns,
                        "Descriptions": {lang: dfs[lang].loc[idx, "Description"] for lang in sheets}
                    }
        return proper_nouns_dict

    

    def improved_replace_proper_nouns(self, transcript, target_language):
        """
        改進方法：
        1. 允許 **所有語言** 都進行 **大小寫不敏感** 匹配 (re.IGNORECASE)。
        2. 單詞 Proper Noun 使用 `\b` 確保獨立匹配，允許標點符號變體 (e.g., `BigQuery.`)。
        3. 多詞 Proper Noun 允許變體空白匹配 (e.g., `CloudFunction`、`Cloud  Function`)。
        """
        replacement_log = []
        updated_transcript = transcript  # 逐步更新文本

        # 🔹 **完全去除 `en-US` 和 `de-DE` 的大小寫敏感設定** 🔹
        case_sensitive = False  # 所有語言都設為不區分大小寫

        for en_term, metadata in self.proper_nouns_dict.items():
            target_proper = metadata["Proper Nouns"].get(target_language)
            if not target_proper:
                continue

            # 收集所有語言版本的 Proper Noun，依長度由長到短排序
            variants = sorted(set(metadata["Proper Nouns"].values()), key=lambda x: len(x), reverse=True)
            pattern_parts = []
            
            for v in variants:
                v_clean = v.strip()
                is_ascii = all(ord(ch) < 128 for ch in v_clean)  # 判斷是否為純 ASCII
                contains_space = " " in v_clean  # 判斷是否為多詞

                if is_ascii and not contains_space:
                    # **單詞 Proper Noun (如 BigQuery) -> 使用 `\b` 但允許標點符號變體**
                    pattern_parts.append(r'\b' + re.escape(v_clean) + r'[\b,.!?]?')
                else:
                    # **多詞 Proper Noun (如 Cloud Function) -> 允許變體空格**
                    pattern_parts.append(re.escape(v_clean).replace(r'\ ', r'\s*'))

            # 組合正則表達式
            combined_pattern = "|".join(pattern_parts)

            # **使用大小寫不敏感匹配 (`re.IGNORECASE`)**
            pattern_regex = re.compile(combined_pattern, re.IGNORECASE)

            # 進行匹配
            matches = pattern_regex.findall(updated_transcript)
            count = len(matches)
            if count > 0:
                # **將所有匹配到的 Proper Noun 用 {目標 proper noun} 替換**
                updated_transcript = pattern_regex.sub("{" + target_proper + "}", updated_transcript)
                log_entry = {
                    "Proper Noun": target_proper,
                    "Original Variants": variants,
                    "Type": metadata.get("Type", ""),
                    "Description": metadata["Descriptions"].get(target_language, ""),
                    "Count": count
                }
                replacement_log.append(log_entry)

        return updated_transcript, replacement_log


    def translate_with_vertex_ai(self, text, target_language):
        """
        使用 Gemini 模型進行翻譯：
          - 將所有不在大括號 {} 中的部分翻譯成目標語言，
          - 保留 {} 中的內容不變，
          - 翻譯結果中不包含大括號（後續會移除）。
        """
        language_prompt_map = {
            "cmn-Hant-TW": "繁體中文",
            "en-US": "英文",
            "ja-JP": "日文",
            "de-DE": "德文"
        }
        lang = language_prompt_map.get(target_language, "繁體中文")

        prompt = (
            f"請將下列文本全部翻譯成{lang}，"
            "請注意：文本中用大括號 {} 包含的部分必須保持原樣，"
            "其餘部分請完整翻譯且不要保留任何原文，"
            "翻譯結果中請不要包含大括號，請僅回傳翻譯後的文本：\n"
            f"{text}"
        )
        try:
            model = GenerativeModel("gemini-1.5-pro-002")
            response = model.generate_content(prompt)
        except Exception as e:
            print(f"Error: {e}")
            print("Switching to an older model version...")
            model = GenerativeModel("gemini-1.5-pro-001")
            response = model.generate_content(prompt)
        
        return response.text

    def process(self):
        """
        完整處理逐字稿流程：
          1. 先進行 proper noun 替換（並以 {} 包裹）。
          2. 呼叫 Gemini 模型翻譯（翻譯時保留 {} 中內容不變）。
          3. 移除翻譯結果中可能殘留的 {}。
          4. 分別儲存翻譯後的逐字稿、proper noun 計數檔及描述檔。
        """
        # (1) Proper noun 替換
        replaced_transcript, replacement_log = self.improved_replace_proper_nouns(self.transcript_text, self.target_language)
        # (2) 呼叫 Gemini 翻譯（保留 {} 中內容不變）
        translated_transcript = self.translate_with_vertex_ai(replaced_transcript, self.target_language)
        # (3) 移除翻譯結果中可能殘留的大括號
        final_transcript = translated_transcript.replace("{", "").replace("}", "")

        # 儲存翻譯後的逐字稿
        with open(f"./results/{self.output_transcript_path}", "w", encoding="utf-8") as file:
            file.write(final_transcript)

        # (a) 儲存 proper noun 計數檔：每個 proper noun 依出現次數寫入多行
        noun_filename = f"./results/term_{self.target_language}.txt"
        with open(noun_filename, "w", encoding="utf-8") as f:
            for entry in replacement_log:
                for _ in range(entry["Count"]):
                    f.write(entry["Proper Noun"] + "\n")

        # (b) 儲存 proper noun 描述檔：同一個 proper noun 只保留一次
        desc_filename = f"./results/description_{self.target_language}.txt"
        proper_noun_desc = {}
        for entry in replacement_log:
            noun = entry["Proper Noun"]
            if noun not in proper_noun_desc:
                proper_noun_desc[noun] = entry["Description"]
        with open(desc_filename, "w", encoding="utf-8") as f:
            for noun in sorted(proper_noun_desc.keys()):
                f.write(f"{noun}: {proper_noun_desc[noun]}\n")

        print(f"✅ Proper Noun 替換 & 翻譯完成！結果儲存至: {self.output_transcript_path}")
        print(f"✅ 偵測 proper noun 檔案產生完成：{noun_filename} 與 {desc_filename}")
    def detect_proper_nouns_with_prompt(self, transcript):
        """
        將 Excel 中所有 proper noun（四個語言版本）放入 prompt，
        請模型偵測逐字稿中出現的 proper noun 及其次數，
        並計算處理所花費的時間，
        最後直接回傳 JSON 格式的字串，例如：
        {
        "DDR Ratio": "3",
        "DP": "3",
        "Nachtschicht": "1",
        "EC": "3",
        "Cloud Function": "1",
        "BigQuery": "1",
        "time": "5.66 s"
        }
        """
        import time
        import json

        # 開始計時
        start_time = time.time()

        # 從 proper_nouns_dict 中擷取所有語言版本的 proper noun 列表
        proper_nouns_list = []
        for metadata in self.proper_nouns_dict.values():
            for lang, pn in metadata["Proper Nouns"].items():
                if pn:
                    proper_nouns_list.append(pn.strip())
        # 去除重複並組合成一個字串
        proper_nouns_list = list(set(proper_nouns_list))
        proper_nouns_str = ", ".join(sorted(proper_nouns_list, key=lambda x: len(x), reverse=True))
        # print(f"proper_nouns_str: {proper_nouns_str}")  

        # 建構 prompt：告知模型只需檢查清單中的 proper noun
        prompt = (
            f"以下是 proper noun 清單：{proper_nouns_str}\n"
            "請分析下面的逐字稿，找出清單中所有出現過的 proper noun，並計算它們出現的次數。\n"
            "請只考慮上述清單中的詞，並以 JSON 格式輸出，例如：\n"
            '[{"proper_noun": "ProperNoun", "count": occurrence_count}, ...]\n'
            f"逐字稿內容：\n{transcript}"
        )
        
        try:
            model = GenerativeModel("gemini-1.5-pro-002")
            response = model.generate_content(prompt)
        except Exception as e:
            print(f"Error: {e}")
            print("Switching to an older model version...")
            model = GenerativeModel("gemini-1.5-pro-001")
            response = model.generate_content(prompt)
        
        raw_output = response.text
        # 結束計時
        end_time = time.time()
        execution_time = end_time - start_time

        # 處理 raw_output：移除可能存在的 code block 格式
        cleaned_result = raw_output.strip()
        if cleaned_result.startswith("```json"):
            cleaned_result = "\n".join(cleaned_result.splitlines()[1:-1])
        try:
            detection_list = json.loads(cleaned_result)
            # 將列表轉換為字典：key 為 proper_noun，value 為 count
            detection_dict = {entry["proper_noun"]: entry["count"] for entry in detection_list}
        except Exception as e:
            print("無法解析 detection_result 為 JSON，使用空結果。", e)
            detection_dict = {}
        
        # 將處理時間加入結果中（四捨五入到 2 位小數）
        detection_dict["time"] = f"{round(execution_time, 2)} s"
        
        # 直接回傳格式化的 JSON 字串
        return json.dumps(detection_dict, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # 直接指定輸入的 txt 檔案路徑
    transcript_file = "transcript.txt"
    
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    # 指定 target_language，例如 "cmn-Hant-TW" 或 "en-US"
    target_language = "en-US"

    # 建立 TranscriptProcessor 實例 (請確認 Excel 路徑正確)
    processor = TranscriptProcessor(
        transcript_text=transcript_text,
        target_language=target_language,
        excel_path="../dataset/Training/Knowledge Dataset.xlsx",
        project_id="hackathon-450410",
        location="us-central1"
    )

    # 呼叫 detect_proper_nouns_with_prompt 並直接印出 JSON 格式的輸出結果
    result_json = processor.detect_proper_nouns_with_prompt(transcript_text)
    print(result_json)
