import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
from google.cloud import speech
from google.cloud import translate_v2 as translate
from transcript_processor import TranscriptProcessor

class AudioTranscriber:
    def __init__(self, project_id="hackathon-450410", output_dir="chunks"):
        """
        初始化 AudioTranscriber 物件
          project_id: Google Cloud Project ID
          output_dir: 用於暫存（或存放完整音檔）與存放結果檔的資料夾
        """
        self.client = speech.SpeechClient()
        self.translate_client = translate.Client()
        self.project_id = project_id
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.zh_transcript_processor = TranscriptProcessor("", "cmn-Hant-TW")
        self.en_transcript_processor = TranscriptProcessor("", "en-US")
        self.ja_transcript_processor = TranscriptProcessor("", "ja-JP")
        self.de_transcript_processor = TranscriptProcessor("", "de-DE")

    def transcribe_segment_enhanced(self, segment):
        audio_content=segment.raw_data
        audio_obj = speech.RecognitionAudio(content=audio_content)
        #### first stage detecttion and transcribe
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=segment.frame_rate,
            language_code="en-US",
            alternative_language_codes=["ja-JP", "de-DE", "cmn-Hant-TW"],
            use_enhanced=True
        )
        response = self.client.recognize(config=config, audio=audio_obj)
        raw_text = ""
        chinese = ""
        english = ""
        japanese = ""
        german = ""
        print(f"len(response.results): {len(response.results)}")
        if len(response.results) >0:
            result= response.results[0]
            transcript = result.alternatives[0].transcript
            # print(f"[Server] 原始辨識結果：{transcript}")
            detection = self.translate_client.detect_language(transcript)
            google_lang_code = detection["language"]
            confidence = detection.get("confidence", "N/A")
            # print(f"[Server] 偵測語言：{google_lang_code} (信心值: {confidence})")
            lang_map = {
                "zh-CN": "cmn-Hant-TW", 
                "zh-TW": "cmn-Hant-TW", 
                "cmn-Hant": "cmn-Hant-TW",
                "en": "en-US", 
                "en-US": "en-US",
                "ja": "ja-JP", 
                "ja-JP": "ja-JP",
                "de": "de-DE", 
                "de-DE": "de-DE"
            }
            detected_lang = lang_map.get(google_lang_code, "en-US")

            #### second stage detection and transcribe
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=segment.frame_rate,
                language_code=detected_lang,
                alternative_language_codes=["en-US"],
                use_enhanced=True
            )
            response = self.client.recognize(config=config, audio=audio_obj)
            if len(response.results) >0:
                result= response.results[0]
                transcript = result.alternatives[0].transcript
                print(f"[Server] 原始辨識結果：{transcript}")
                raw_text += transcript + "\n"
                detection = self.translate_client.detect_language(transcript)
                google_lang_code = detection["language"]
                confidence = detection.get("confidence", "N/A")
                print(f"[Server] 偵測語言：{google_lang_code} (信心值: {confidence})")
                detected_lang = lang_map.get(google_lang_code, "en-US")
                print(f"[Server] 轉換後的語言標籤: {detected_lang}")

                # **翻譯不同語言**
                translations = {
                    "cmn-Hant-TW": chinese,
                    "en-US": english,
                    "ja-JP": japanese,
                    "de-DE": german
                }

                for target_lang in translations.keys():
                    if detected_lang == target_lang:
                        translations[target_lang] += transcript + "\n"
                    else:
                        translation = self.translate_client.translate(transcript, target_language=target_lang)
                        translations[target_lang] += translation["translatedText"] + "\n"

                chinese, english, japanese, german = translations["cmn-Hant-TW"], translations["en-US"], translations["ja-JP"], translations["de-DE"]

        # **遍歷 "cmn-Hant-TW"、"en-US"、"ja-JP"、"de-DE"，偵測 proper noun**
        proper_nouns_detected = {}
        for lang, processor in zip(["cmn-Hant-TW", "en-US", "ja-JP", "de-DE"], [self.zh_transcript_processor, self.en_transcript_processor, self.ja_transcript_processor, self.de_transcript_processor]):
            _, replacement_log = processor.improved_replace_proper_nouns(raw_text, lang)

            # **收集 Proper Nouns 和對應描述**
            proper_noun_entries = []
            for entry in replacement_log:
                noun = entry["Proper Noun"]
                desc = entry["Description"]
                proper_noun_entries.append(f"{noun} ({desc})" if desc else noun)

            proper_nouns_detected[lang] = ", ".join(proper_noun_entries) if proper_noun_entries else ""

        # **組合最終的回傳字串**
        result_str = (
            f"RAW: {raw_text.strip()}\n"
            f"中文: {chinese.strip()}\n"
            f"英文: {english.strip()}\n"
            f"日文: {japanese.strip()}\n"
            f"德文: {german.strip()}\n"
            f"中文 專有名詞: {proper_nouns_detected['cmn-Hant-TW']}\n"
            f"英文 專有名詞: {proper_nouns_detected['en-US']}\n"
            f"日文 專有名詞: {proper_nouns_detected['ja-JP']}\n"
            f"德文 專有名詞: {proper_nouns_detected['de-DE']}\n"
        )

        return result_str, raw_text, chinese, english, japanese, german, proper_nouns_detected["cmn-Hant-TW"], proper_nouns_detected["en-US"], proper_nouns_detected["ja-JP"], proper_nouns_detected["de-DE"]





    def transcribe_segment(self, segment):
        """
        對單一音訊 segment（AudioSegment 物件，約 2~3 秒）進行語音辨識、語種偵測與翻譯，
        並在辨識完成後，使用 `TranscriptProcessor` 偵測 proper nouns，確保 proper nouns 保持一致。
        
        返回: (result_str, raw_text, chinese, english, japanese, german)
        """
        # 取得音訊原始 bytes
        audio_content = segment.raw_data
        audio_obj = speech.RecognitionAudio(content=audio_content)

        # 設定辨識參數
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=segment.frame_rate,
            language_code="en-US",
            alternative_language_codes=["ja-JP", "de-DE", "cmn-Hant-TW"],
            use_enhanced=True
        )
        response = self.client.recognize(config=config, audio=audio_obj)

        raw_text = ""
        chinese = ""
        english = ""
        japanese = ""
        german = ""

        print(f"len(response.results): {len(response.results)}")

        for result in response.results:
            transcript = result.alternatives[0].transcript
            print(f"[Server] 原始辨識結果：{transcript}")
            raw_text += transcript + "\n"

            # 偵測語言
            detection = self.translate_client.detect_language(transcript)
            google_lang_code = detection["language"]
            confidence = detection.get("confidence", "N/A")
            print(f"[Server] 偵測語言：{google_lang_code} (信心值: {confidence})")

            # **將 Google 語言代碼轉換為 `TranscriptProcessor` 所需格式**
            lang_map = {
                "zh-CN": "cmn-Hant-TW", 
                "zh-TW": "cmn-Hant-TW", 
                "cmn-Hant": "cmn-Hant-TW",
                "en": "en-US", 
                "en-US": "en-US",
                "ja": "ja-JP", 
                "ja-JP": "ja-JP",
                "de": "de-DE", 
                "de-DE": "de-DE"
            }
            detected_lang = lang_map.get(google_lang_code, "en-US")  # 預設為 "en-US"

            print(f"[Server] 轉換後的語言標籤: {detected_lang}")

            # **翻譯不同語言**
            translations = {
                "cmn-Hant-TW": chinese,
                "en-US": english,
                "ja-JP": japanese,
                "de-DE": german
            }

            for target_lang in translations.keys():
                if detected_lang == target_lang:
                    translations[target_lang] += transcript + "\n"
                else:
                    translation = self.translate_client.translate(transcript, target_language=target_lang)
                    translations[target_lang] += translation["translatedText"] + "\n"

            chinese, english, japanese, german = translations["cmn-Hant-TW"], translations["en-US"], translations["ja-JP"], translations["de-DE"]

        # **遍歷 "cmn-Hant-TW"、"en-US"、"ja-JP"、"de-DE"，偵測 proper noun**
        proper_nouns_detected = {}
        for lang, processor in zip(["cmn-Hant-TW", "en-US", "ja-JP", "de-DE"], [self.zh_transcript_processor, self.en_transcript_processor, self.ja_transcript_processor, self.de_transcript_processor]):
            _, replacement_log = processor.improved_replace_proper_nouns(raw_text, lang)

            # **收集 Proper Nouns 和對應描述**
            proper_noun_entries = []
            for entry in replacement_log:
                noun = entry["Proper Noun"]
                desc = entry["Description"]
                proper_noun_entries.append(f"{noun} ({desc})" if desc else noun)

            proper_nouns_detected[lang] = ", ".join(proper_noun_entries) if proper_noun_entries else ""

        # **組合最終的回傳字串**
        result_str = (
            f"RAW: {raw_text.strip()}\n"
            f"中文: {chinese.strip()}\n"
            f"英文: {english.strip()}\n"
            f"日文: {japanese.strip()}\n"
            f"德文: {german.strip()}\n"
            f"中文 專有名詞: {proper_nouns_detected['cmn-Hant-TW']}\n"
            f"英文 專有名詞: {proper_nouns_detected['en-US']}\n"
            f"日文 專有名詞: {proper_nouns_detected['ja-JP']}\n"
            f"德文 專有名詞: {proper_nouns_detected['de-DE']}\n"
        )

        return result_str, raw_text, chinese, english, japanese, german, proper_nouns_detected["cmn-Hant-TW"], proper_nouns_detected["en-US"], proper_nouns_detected["ja-JP"], proper_nouns_detected["de-DE"]

    def process_audio_by_silence(self, audio_path, min_silence_len=300, silence_thresh=-45, format="wav"):
        """
        精確辨識流程：
          1. 讀取完整音檔，利用 pydub 根據靜音切分（split_on_silence）。
          2. 對每一個切出的 chunk 進行語音辨識與翻譯。
        返回: (total_raw, total_chinese, total_english, total_japanese, total_german)
        """
        audio = AudioSegment.from_file(audio_path, format=format)
        chunks = split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        print(f"[Server] 共分割出 {len(chunks)} 個段落 (依靜音切分)")
        total_raw = ""
        total_chinese = ""
        total_english = ""
        total_japanese = ""
        total_german = ""
        for i, chunk in enumerate(chunks):
            print(f"[Server] 處理 silence chunk {i}")
            # 只累積各語系結果，不必組合即時回傳的字串
            _, raw_text, chinese, english, japanese, german, proper_nouns_zh, proper_nouns_en, proper_nouns_ja, proper_nouns_de = self.transcribe_segment(chunk)
            total_raw += raw_text + "\n"
            total_chinese += chinese + "\n"
            total_english += english + "\n"
            total_japanese += japanese + "\n"
            total_german += german + "\n"
        return total_raw, total_chinese, total_english, total_japanese, total_german

    def save_results_separate(self, raw_text, chinese_text, english_text, japanese_text, german_text, output_folder="results"):
        """
        將辨識結果分別存成文字檔到指定的資料夾：
         - 原始文字存 raw_text_precise.txt
         - 中文存 chinese_precise.txt
         - 英文存 english_precise.txt
         - 日文存 japanese_precise.txt
         - 德文存 german_precise.txt
        """
        os.makedirs(output_folder, exist_ok=True)
        raw_file_path = os.path.join(output_folder, "raw_text_precise.txt")
        chinese_file_path = os.path.join(output_folder, "cmn-Hant-TW_precise.txt")
        english_file_path = os.path.join(output_folder, "en-US_precise.txt")
        japanese_file_path = os.path.join(output_folder, "ja-JP_precise.txt")
        german_file_path = os.path.join(output_folder, "de-DE_precise.txt")
        
        with open(raw_file_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        with open(chinese_file_path, "w", encoding="utf-8") as f:
            f.write(chinese_text)
        with open(english_file_path, "w", encoding="utf-8") as f:
            f.write(english_text)
        with open(japanese_file_path, "w", encoding="utf-8") as f:
            f.write(japanese_text)
        with open(german_file_path, "w", encoding="utf-8") as f:
            f.write(german_text)
        print(f"[Server] 結果已分別存成以下檔案：")
        print(f"         {raw_file_path}")
        print(f"         {chinese_file_path}")
        print(f"         {english_file_path}")
        print(f"         {japanese_file_path}")
        print(f"         {german_file_path}")