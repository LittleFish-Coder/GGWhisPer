from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
import socketio
from datetime import datetime
from io import BytesIO
from pydub import AudioSegment
# from summarizer import MeetingSummarizer
from summarizer_RAG import MeetingSummarizer    # update with stronger version RAG
from utils import download_transcript, upload_summary, download_wav, upload_transcript, upload_term, upload_description, download_description, download_summary, upload_wav
from audio_transcriber import AudioTranscriber
# from transcript_processor import TranscriptProcessor
from transcript_processor_enhanced import TranscriptProcessor
from chatbot_RAG import Chatbot
from text_to_speech import TextToSpeech
import uvicorn
import json

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 創建 FastAPI 應用
app = FastAPI(title="GGWhisPer AI Backend")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建 Socket.IO 服務器
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],  # 允許所有來源
    logger=True,
    engineio_logger=True
)

# 創建 Socket.IO 應用
socket_app = socketio.ASGIApp(sio, app)

# 初始化 services
# project_id = "hackathon-450410"
project_id = "hackathon-450900"
transcriber = AudioTranscriber(project_id=project_id)
chatbot = Chatbot(project_id=project_id, knowledge_file="knowledge.xlsx")
summarizer = MeetingSummarizer(project_id=project_id, knowledge_file="knowledge.xlsx")
text_to_speech = TextToSpeech()


# 存儲會議內容
meeting_contents: Dict[str, List[Dict]] = {}

@sio.event
async def connect(sid, environ):
    """當客戶端連接時"""
    print(f"Client connected: {sid}")
    meeting_contents[sid] = []
    await sio.emit('connect_response', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid):
    """當客戶端斷開連接時"""
    print(f"Client disconnected: {sid}")
    if sid in meeting_contents:
        del meeting_contents[sid]

@sio.event
async def audio_data(sid, data):
    """處理接收到的音訊數據"""
    print(f"Received audio data from {sid}, size: {len(data) if data else 0} bytes")
    try:

        # print header
        # print(data[:40])

        # 將二進制數據轉換為 AudioSegment
        audio_io = BytesIO(data)
        # print(audio_io[:4])
        segment = AudioSegment.from_file(audio_io, format='wav')

        # 處理音訊數據
        result_str, raw_text, chinese, english, japanese, german, proper_nouns_chinese, proper_nouns_english, proper_nouns_japanese, proper_nouns_german = transcriber.transcribe_segment(segment)
        print(result_str)
        proper_nouns_chinese += '\n'
        proper_nouns_english += '\n'
        proper_nouns_japanese += '\n'
        proper_nouns_german += '\n'
        print(f"raw_text: {raw_text}")
        print(f"chinese: {chinese}")
        print(f"english: {english}")
        print(f"japanese: {japanese}")
        print(f"german: {german}")
        print(f"proper_nouns_chinese: {proper_nouns_chinese}")
        print(f"proper_nouns_english: {proper_nouns_english}")
        print(f"proper_nouns_japanese: {proper_nouns_japanese}")
        print(f"proper_nouns_german: {proper_nouns_german}")
        
        # 儲存轉寫結果
        meeting_contents[sid].append({
            "type": "transcription",
            "raw_text": raw_text.strip(),
            "chinese": chinese.strip(),
            "english": english.strip(),
            "japanese": japanese.strip(),
            "german": german.strip(),
            "proper_nouns_chinese": proper_nouns_chinese,
            "proper_nouns_english": proper_nouns_english,
            "proper_nouns_japanese": proper_nouns_japanese,
            "proper_nouns_german": proper_nouns_german,
            "timestamp": datetime.now().isoformat()
        })

        # 發送結果回客戶端
        await sio.emit('transcription_response', {
            "type": "transcription",
            "raw_text": raw_text.strip(),
            "chinese": chinese.strip(),
            "english": english.strip(),
            "japanese": japanese.strip(),
            "german": german.strip(),
            "proper_nouns_chinese": proper_nouns_chinese,
            "proper_nouns_english": proper_nouns_english,
            "proper_nouns_japanese": proper_nouns_japanese,
            "proper_nouns_german": proper_nouns_german,
        }, room=sid)

    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        await sio.emit('error', {
            "type": "error",
            "message": str(e)
        }, room=sid)

@sio.event
async def get_meeting_content(sid):
    """獲取會議內容"""
    content = meeting_contents.get(sid, [])
    await sio.emit('meeting_content', {
        "success": True,
        "content": content
    }, room=sid)


# inference with audio wav file
@app.get("/inference/{audio_id}")
async def inference_audio(audio_id: str, background_tasks: BackgroundTasks):
    """Inference with audio wav file"""
    try:
        BUCKET_NAME = "hackathon-c2"
        if not audio_id.isdigit():
            audio_id = "Training"
        
        download_wav(BUCKET_NAME, audio_id)
        audio_path = f"./{audio_id}.wav"
        
        # inference with AudioTranscriber and TranscriptProcessor
        total_raw, total_chinese, total_english, total_japanese, total_german = transcriber.process_audio_by_silence(audio_path)
        transcriber.save_results_separate(total_raw, total_chinese, total_english, total_japanese, total_german, output_folder="results")
        upload_transcript(BUCKET_NAME, audio_id, "raw", "results/raw_text_precise.txt")


        for lang in ["cmn-Hant-TW", "en-US","ja-JP", "de-DE"]:
            """
            結束後 將會有以下檔案
            language: [cmn-Hant-TW, en-US, ja-JP, de-DE]
            results/
            ├── transcript_language.txt
            ├── term_language.txt
            └── description_language.txt
            """
            print(f"[Server] 處理 proper noun 替換與翻譯，目標語言：{lang}")
            processor = TranscriptProcessor(total_raw, lang, project_id=project_id)
            processor.process()
            # 上傳對應語言的 transcript, term, description
            upload_corresponing_trascript_term_description(audio_id, lang, background_tasks)

        # return success message (upload to GCS)
        response = {
            "message": "Inference success"
        }

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/term/{file_id}")
def term_file(file_id: str, background_tasks: BackgroundTasks):
    BUCKET_NAME = "hackathon-c2"
    lang = ["zh", "en", "ja", "de"]
    term_description = {l: [] for l in lang}
    
    for l in lang:
        try:
            print(f"正在處理語言：{l}")
            download_description(BUCKET_NAME, file_id, l)
            
            # 嘗試不同編碼
            encodings = ['utf-8', 'utf-8-sig', 'big5', 'gb18030']
            
            for encoding in encodings:
                try:
                    with open(f"{file_id}.txt", "r", encoding=encoding) as f:
                        lines = f.readlines()
                        for line in lines:
                            if ":" in line:
                                term, description = line.split(":", 1)
                                term_description[l].append({
                                    "term": term.strip(),
                                    "description": description.strip()
                                })
                        break  # 如果成功讀取，跳出編碼嘗試循環
                except UnicodeDecodeError:
                    continue
            print(f"語言：{l} 處理完畢")        
        except Exception as e:
            print("Error: ", str(e))
            # 發生錯誤時，該語言保持空列表

    # download the python dict to json to local
    with open(f"{file_id}.json", "w", encoding="utf-8") as f:
        json.dump(term_description, f, ensure_ascii=False)
            
    return term_description

@app.get("/transcript/{file_id}")
def transcript_file(file_id: str, background_tasks: BackgroundTasks):
    BUCKET_NAME = "hackathon-c2"
    lang = ["raw", "zh", "en", "ja", "de"]
    # dict of list
    transcript = {l: [] for l in lang}
    for l in lang:
        try:
            download_transcript(BUCKET_NAME, file_id, l)
            with open(f"{file_id}.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    transcript[l].append(line.strip())
        except Exception as e:
            print("Error: ", str(e))
    return transcript

@app.get("/summarize/{file_id}")
async def summarize_file(file_id: str, background_tasks: BackgroundTasks):
    """Summarize transcript file"""
    try:
        BUCKET_NAME = "hackathon-c2"
        if not file_id.isdigit():
            file_id = "meeting_transcript"

        try:    # download summary from GCS first
            download_summary(BUCKET_NAME, file_id, "zh")
            with open(f"{file_id}.md", "r", encoding="utf-8") as f:
                summary = f.read()
            response = {
                "markdown": summary
            }
            print(f"The file {file_id}.md already exists in GCS.")
            print(f"Returning the summary instantly.")
            return response
        except Exception as e:
            print("Error: ", str(e))

        download_transcript(BUCKET_NAME, file_id=file_id)
        with open(f"{file_id}.txt", "r", encoding="utf-8") as f:
            transcript = f.read()
        summary = summarizer.summarize(transcript)

        print(summary.markdown)
        
        response = {
            "markdown": summary.markdown
        }

        # run in background
        upload_summary(BUCKET_NAME, f"{file_id}", "zh", summary.markdown)
        # background_tasks.add_task(upload_summary, BUCKET_NAME, f"{file_id}", "zh", summary.markdown)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatbotRequest(BaseModel):
    query: str

# chatbot API
@app.post("/chatbot")
async def query_chatbot(query: str):
    """Query the chatbot with a plain string input"""
    try:
        response, has_terms = await chatbot.answer_query(query)
        print(f"Query: {query}")
        print(f"Response: {response}")
        print(f"Has terms: {has_terms}")
        return {"reply": response, "term": has_terms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def home():
    return RedirectResponse(url="/docs")

# 將 socket_app 掛載到 FastAPI 應用
app.mount("/", socket_app)

def summarize_instant(file_id: str, content: str, background_tasks: BackgroundTasks):
    BUCKET_NAME = "hackathon-c2"
    summary = summarizer.summarize(content)
    # background_tasks.add_task(upload_summary, BUCKET_NAME, f"{file_id}", "zh", summary.markdown)
    upload_summary(BUCKET_NAME, f"{file_id}", "zh", summary.markdown)
    return summary.markdown

def upload_corresponing_trascript_term_description(file_id: str, lang: str, background_tasks: BackgroundTasks):
    BUCKET_NAME = "hackathon-c2"

    lang_gcs = {
        "cmn-Hant-TW": "zh",
        "en-US": "en",
        "ja-JP": "ja",
        "de-DE": "de"
    }

    # upload transcript
    try:
        upload_transcript(BUCKET_NAME, file_id, lang_gcs[lang], f"results/transcript_{lang}.txt")
        # text 2 speech and upload to GCS
        convert_to_speech_to_gcs(f"results/transcript_{lang}.txt", file_id, lang_gcs[lang], background_tasks)
        # background_tasks.add_task(convert_to_speech_to_gcs, f"results/transcript_{lang}.txt", file_id, lang_gcs[lang], background_tasks)
    except Exception as e:
        print(f"Error: {str(e)}")
        upload_transcript(BUCKET_NAME, file_id, lang_gcs[lang], f"results/{lang}_precise.txt")
        # text 2 speech and upload to GCS
        convert_to_speech_to_gcs(f"results/{lang}_precise.txt", file_id, lang_gcs[lang], background_tasks)
        # background_tasks.add_task(convert_to_speech_to_gcs, f"results/{lang}_precise.txt", file_id, lang_gcs[lang], background_tasks)

    if lang == "cmn-Hant-TW":
        try:
            # do summarization silently
            with open("results/transcript_cmn-Hant-TW.txt", "r", encoding="utf-8") as f:
                content = f.read()
                summary = summarize_instant(file_id, content, background_tasks)
        except Exception as e:
            print(f"Error: {str(e)}")
            with open("results/cmn-Hant-TW_precise.txt", "r", encoding="utf-8") as f:
                content = f.read()
                summary = summarize_instant(file_id, content, background_tasks)
    
    # upload term
    try:
        upload_term(BUCKET_NAME, file_id, lang_gcs[lang], f"results/gemini_detection_{lang}.txt")
    except Exception as e:
        print(f"Error: results/term_{lang}.txt - {str(e)}")
        upload_term(BUCKET_NAME, file_id, lang_gcs[lang], f"results/term_{lang}.txt")
    # upload description
    upload_description(BUCKET_NAME, file_id, lang_gcs[lang], f"results/description_{lang}.txt")

def convert_to_speech_to_gcs(transcript_file: str, file_id: str, lang: str, background_tasks: BackgroundTasks):
    BUCKET_NAME = "hackathon-c2"
    try:
        audio_path = text_to_speech.convert(transcript_file, lang, file_id)
        upload_wav(BUCKET_NAME, file_id, audio_path, lang)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)