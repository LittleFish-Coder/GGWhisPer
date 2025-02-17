import pandas as pd
import re
import vertexai
from vertexai.generative_models import GenerativeModel
import os
import time
import json
class TranscriptProcessor:
    def __init__(self, transcript_text, target_language, 
                 excel_path="../dataset/Training/Knowledge Dataset.xlsx",
                 project_id="hackathon-450900", location="us-central1", dir="results"):
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
        # dir = "results"
        os.makedirs(dir, exist_ok=True)
        self.dir = dir
        # 初始化 Vertex AI 環境
        vertexai.init(project=self.project_id, location=self.location)
        # 讀取 Excel 並建立 proper_nouns_dict
        self.proper_nouns_dict = self.load_proper_nouns()
        # 定義輸出逐字稿檔案名稱
        self.output_transcript_path = f"transcript_{self.target_language}.txt"

    def load_proper_nouns(self):
        """
        讀取 Excel 並建立 `proper_nouns_dict` 和 `all_proper_nouns_dict`
        - `proper_nouns_dict` 以 `en-US` 為 key，存入所有語言對應版本的 Proper Noun 和描述。
        - `all_proper_nouns_dict` 允許從 **任何語言版本的 Proper Noun 找到 `en-US` key**，確保所有語言都能匹配。
        """
        sheets = ["cmn-Hant-TW", "en-US", "ja-JP", "de-DE"]
        
        # 讀取 Excel，每個 sheet 移除欄位前後空白
        dfs = {
            sheet: pd.read_excel(self.excel_path, sheet_name=sheet).rename(columns=lambda x: x.strip())
            for sheet in sheets
        }

        proper_nouns_dict = {}
        all_proper_nouns_dict = {}

        for idx in dfs["en-US"].index:
            en_proper_noun = dfs["en-US"].loc[idx, "Proper Noun"]
            
            if pd.notna(en_proper_noun):
                proper_nouns = {}
                descriptions = {}

                for sheet in sheets:
                    pn = dfs[sheet].loc[idx, "Proper Noun"]
                    desc = dfs[sheet].loc[idx, "Description"]

                    if pd.notna(pn):
                        proper_nouns[sheet] = pn.strip()  # Proper Noun
                        all_proper_nouns_dict[pn.strip()] = en_proper_noun  # 反向映射到 `en-US`

                    descriptions[sheet] = desc.strip() if pd.notna(desc) else "N/A"  # Description

                if proper_nouns:
                    proper_nouns_dict[en_proper_noun] = {
                        "Type": dfs["en-US"].loc[idx, "Type"],
                        "Proper Nouns": proper_nouns,
                        "Descriptions": descriptions
                    }

        self.all_proper_nouns_dict = all_proper_nouns_dict  # 存為類別變數，方便查找
        return proper_nouns_dict



    def improved_replace_proper_nouns(self, transcript, target_language):
        """
        改進方法（逐行偵測 proper noun）：
        1. 從 proper_nouns_dict 中讀取所有 proper noun（各語言版本）。
        2. 針對每個項目，依據所有變體建立一組命名群組（named group），使用自訂邊界處理英文及中文混雜情況。
        3. 逐行使用 re.sub 搭配替換函式進行替換，同時記錄出現的 proper noun（依原始順序）。
        4. 回傳替換後的逐字稿、依順序的 proper noun 清單 與處理時間。
        """
        start_time = time.time()
        
        # 建立命名群組與對應 proper noun 資訊
        group_patterns = []
        group_mapping = {}
        i = 0
        for en_term, metadata in self.proper_nouns_dict.items():
            target_proper = metadata["Proper Nouns"].get(target_language) or metadata["Proper Nouns"].get("en-US")
            if not target_proper:
                continue
            
            variants = sorted(set(metadata["Proper Nouns"].values()), key=lambda x: len(x), reverse=True)
            variant_patterns = []
            for v in variants:
                v_clean = v.strip()
                is_ascii = all(ord(ch) < 128 for ch in v_clean)
                contains_space = " " in v_clean
                if is_ascii and not contains_space:
                    left_boundary = r'(?:(?<=^)|(?<=[^A-Za-z0-9]))'
                    right_boundary = r'(?=$|[^A-Za-z0-9])'
                    variant_patterns.append(left_boundary + re.escape(v_clean) + right_boundary)
                else:
                    variant_patterns.append(re.escape(v_clean).replace(r'\\ ', r'\\s+'))
            combined_entry_pattern = "(" + "|".join(variant_patterns) + ")"
            group_name = f"pn_{i}"
            i += 1
            group_patterns.append(f"(?P<{group_name}>" + combined_entry_pattern + ")")
            group_mapping[group_name] = {
                "Proper Noun": target_proper,
                "Original Variants": variants,
                "Type": metadata.get("Type", ""),
                "Description": metadata["Descriptions"].get(target_language, ""),
                "Count": 0
            }
        
        if not group_patterns:
            execution_time = round(time.time() - start_time, 2)
            return transcript, [], execution_time
        
        combined_pattern = "|".join(group_patterns)
        regex = re.compile(combined_pattern, re.IGNORECASE)
        
        ordered_detections = []
        
        def replacement_func(match):
            for group_name, value in match.groupdict().items():
                if value is not None:
                    group_mapping[group_name]["Count"] += 1
                    ordered_detections.append(group_mapping[group_name]["Proper Noun"])
                    return "{" + group_mapping[group_name]["Proper Noun"] + "}"
            return match.group(0)
        
        updated_lines = []
        for line in transcript.splitlines():
            new_line = regex.sub(replacement_func, line)
            updated_lines.append(new_line)
        updated_transcript = "\n".join(updated_lines)
        execution_time = round(time.time() - start_time, 2)
        # print(f'order_detections: {ordered_detections}')
        return updated_transcript, ordered_detections, execution_time


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
            "文本為：\n"
            # "翻譯結果中請不要包含大括號，請僅回傳翻譯後的文本"
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
    def detect_proper_nouns_with_prompt(self, transcript):
        start_time = time.time()
        proper_nouns_list = []
        for metadata in self.proper_nouns_dict.values():
            for pn in metadata["Proper Nouns"].values():
                if pn:
                    proper_nouns_list.append(pn.strip())

        proper_nouns_list = sorted(set(proper_nouns_list), key=lambda x: len(x), reverse=True)

        prompt = (
            f"以下是 Proper Noun 清單：{', '.join(proper_nouns_list)}。\n"
            "請分析下面的逐字稿，找出清單中所有出現過的 Proper Noun，並直接在原始文本內替換掉它們。\n"
            "請確保 Proper Noun 使用清單中的標準寫法，若存在變體（如大小寫、縮寫），請統一替換為清單中最標準的名稱。\n"
            "請確保 Proper Noun **重複出現時** 也都包含在 `proper_nouns` 列表中，並且按照它們在逐字稿中 **實際出現的順序** 記錄。\n"
            "請務必輸出 **Python dictionary 格式的 JSON 字符串**（不含任何解釋性文字），格式如下：\n\n"
            "```json\n"
            "{\n"
            '  "transcript": "這裡填入替換後的逐字稿",\n'
            '  "proper_nouns": ["Proper Noun 1", "Proper Noun 2", ...]\n'
            "}\n"
            "```\n\n"
            "請直接輸出 JSON 字符串，不要加入任何其他說明。\n"
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

        cleaned_response = response.text.strip()
        execution_time = round(time.time() - start_time, 2)
        # print(f'cleaned_response: {cleaned_response}')
        try:
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response.strip("```json").strip("```").strip()

            response_json = json.loads(cleaned_response)
            cleaned_transcript = response_json.get("transcript", transcript)
            mapped_detection_list = response_json.get("proper_nouns", [])

            if not isinstance(mapped_detection_list, list):
                mapped_detection_list = []

            # **進行 Proper Noun 替換**
            updated_mapped_list = []
            for proper in mapped_detection_list:
                target_proper = self.get_target_proper_noun(proper, self.target_language)
                updated_mapped_list.append(target_proper)

                # 透過正則表達式替換所有 proper noun 為 {目標語言版本}
                pattern = re.escape(proper).replace(r'\ ', r'\\s+')
                cleaned_transcript = re.sub(pattern, f"{{{target_proper}}}", cleaned_transcript, flags=re.IGNORECASE)

        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤，回退到原始內容: {e}")
            cleaned_transcript = transcript
            updated_mapped_list = []

        detection_result = {
            "proper_nouns": updated_mapped_list,
            "time": f"{execution_time} s"
        }
        # print(f"detection_result: {detection_result} ")

        return cleaned_transcript, detection_result

    def get_target_proper_noun(self, candidate_str, target_language):
        for en_term, metadata in self.proper_nouns_dict.items():
            if candidate_str in metadata["Proper Nouns"].values():
                return metadata["Proper Nouns"].get(target_language, candidate_str)
        return candidate_str


    def replace_gemini_proper_nouns(self, transcript, gemini_proper_list, target_language):
        new_transcript = transcript
        for proper in gemini_proper_list:
            candidate_str = proper if isinstance(proper, str) else proper.get("proper_noun", "")
            target_proper = self.get_target_proper_noun(candidate_str, target_language)
            if target_proper:
                pattern = re.escape(candidate_str).replace(r'\ ', r'\\s+')
                new_transcript = re.sub(pattern, "{" + target_proper + "}", new_transcript, flags=re.IGNORECASE)
        return new_transcript
    def process(self):
        """
        完整處理逐字稿流程：
        1. 先進行 Regular Expression 替換並記錄 Proper Noun 及處理時間。
        2. 使用 Gemini AI 偵測 Proper Noun 並記錄結果及處理時間。
        3. 呼叫 Gemini 模型翻譯（翻譯時保留 {} 中內容不變）。
        4. 移除翻譯結果中可能殘留的 {}。
        5. 儲存翻譯後的逐字稿、proper noun 計數檔及描述檔。
        6. 顯示 Regular Expression 和 Gemini AI 偵測的 Proper Noun 結果。
        """
        replaced_transcript, proper_noun_list_regex, execution_time = self.improved_replace_proper_nouns(self.transcript_text, self.target_language)
        
        # **儲存 Regex 偵測的 Proper Noun**
        regex_filename = f"./{self.dir}/term_{self.target_language}.txt"
        with open(regex_filename, "w", encoding="utf-8") as f:
            f.write(f"Regex Proper Noun 偵測結果 (處理時間: {execution_time} 秒)\n")
            for i, proper_noun in enumerate(proper_noun_list_regex, start=1):
                f.write(f"{i}. {proper_noun}\n")

        # **執行 Gemini Proper Noun 偵測**
        llm_replaced_transcript, detection_result = self.detect_proper_nouns_with_prompt(self.transcript_text)

        # **將 Gemini 偵測的 Proper Noun 也經過 improved_replace_proper_nouns 處理**
        llm_replaced_transcript, testproper_noun_list_regex, testexecution_time = self.improved_replace_proper_nouns(llm_replaced_transcript, self.target_language)

        # **翻譯最終結果**
        translated_transcript = self.translate_with_vertex_ai(llm_replaced_transcript, self.target_language)

        # **儲存 Gemini 偵測的 Proper Noun**
        gemini_detection_filename = f"./{self.dir}/gemini_detection_{self.target_language}.txt"
        with open(gemini_detection_filename, "w", encoding="utf-8") as f:
            f.write(f"Gemini prompt Proper Noun Detection (time: {detection_result['time']})\n")
            f.write("=" * 50 + "\n")
            for i, proper_noun in enumerate(detection_result["proper_nouns"], start=1):
                f.write(f"{i}. {proper_noun}\n")
            f.write("-" * 50 + "\n")

        # **儲存翻譯後的逐字稿**
        final_transcript = translated_transcript.replace("{", "").replace("}", "")
        with open(f"./{self.dir}/{self.output_transcript_path}", "w", encoding="utf-8") as file:
            file.write(final_transcript)

        # **🔹 儲存 Proper Noun 描述檔**
        desc_filename = f"./{self.dir}/description_{self.target_language}.txt"
        
        proper_noun_desc = {}

        for noun in detection_result["proper_nouns"]:
            # 🔹 找到對應的 `en-US` Key
            matched_key = self.all_proper_nouns_dict.get(noun, noun)
            if matched_key:
                # print(f"Matched Key: {matched_key} -> {noun}")
            # 🔹 取得目標語言的 Proper Noun 和描述
                proper_noun_target = self.proper_nouns_dict.get(matched_key, {}).get("Proper Nouns", {}).get(self.target_language, noun)
                description = self.proper_nouns_dict.get(matched_key, {}).get("Descriptions", {}).get(self.target_language, "N/A")

                proper_noun_desc[proper_noun_target] = description

        # 🔹 儲存描述檔
        desc_filename = f"./{self.dir}/description_{self.target_language}.txt"
        with open(desc_filename, "w", encoding="utf-8") as f:
            for noun, description in proper_noun_desc.items():
                f.write(f"{noun}: {description}\n")

if __name__ == "__main__":
    # 直接指定輸入的 txt 檔案路徑

    transcript_file = "Testing_twoStage.txt"
    folder_name = os.path.splitext(transcript_file)[0]
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript_text = f.read()
    # 指定 target_language，例如 "cmn-Hant-TW" 或 "en-US"
    target_language = "cmn-Hant-TW"

    # 建立 TranscriptProcessor 實例 (請確認 Excel 路徑正確)
    processor = TranscriptProcessor(
        transcript_text=transcript_text,
        target_language=target_language,
        excel_path="../dataset/Training/Knowledge Dataset.xlsx",
        project_id="hackathon-450900",
        location="us-central1",
        dir=folder_name
    )

    processor.process()
