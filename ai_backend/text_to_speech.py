from gtts import gTTS
import os

class TextToSpeech:
    def __init__(self):
        """
        初始化 TextToSpeech 類別。
        """
        pass
    
    def convert(self, input_file, target_lang, audio_id=""):
        """
        讀取輸入的文字檔案，並轉換為指定語言的語音檔。
        :param input_file: 要轉換的文字檔案路徑
        :param target_lang: 目標語言代碼（如 'zh-tw', 'en', 'ja', 'de'）
        :return: 生成的音頻檔案路徑
        """

        mapping = {
            "zh": "zh-TW",
            "en": "en",
            "ja": "ja",
            "de": "de"
        }

        target_lang = mapping[target_lang]

        with open(input_file, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # 使用 gTTS 生成語音
        tts = gTTS(text=text, lang=target_lang)
        
        # 確保結果資料夾存在
        output_folder = f"./results/wav/{target_lang}"
        os.makedirs(output_folder, exist_ok=True)
        
        # 儲存為 mp3 檔案
        output_file = os.path.join(output_folder, f"{audio_id}.mp3")
        tts.save(output_file)
        print(f"音頻檔案已保存：{output_file}")
        
        return output_file

if __name__ == "__main__":
    # 測試
    languages = {"cmn-Hant-TW": "zh-tw", "en-US": "en", "ja-JP": "ja", "de-DE": "de"}
    tts = TextToSpeech()
    for lang, code in languages.items():
        tts.convert(f"./results/{lang}_precise.txt", code, "test")
