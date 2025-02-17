from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from crud.audio import AudioCrudManager
from schemas import audio as AudioSchema
import os
import shutil
from datetime import datetime
from fastapi import Form
from google.cloud import storage
import os
from dotenv import load_dotenv
from .depends import check_audio_id
from typing import List, Optional

load_dotenv()

CREDENTIALS_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS", "shared-credentials.json"
)
storage_client = storage.Client.from_service_account_json(CREDENTIALS_PATH)


not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Audio does not exist"
)


AudioCrud = AudioCrudManager()
router = APIRouter(prefix="/audio", tags=["Audio"])


BUCKET_NAME = "hackathon-c2"  # 替換成您的 bucket 名稱


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_audio_with_file(
    info: str = Form(...),
    title: str = Form(...),
    audio_file: UploadFile = File(...),
):
    audio = await AudioCrud.create_with_file(info=info, title=title)
    if not audio_file.filename.lower().endswith(".wav"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only WAV files are allowed"
        )
    try:

        file_name = f"wav/{audio.id}.wav"

        # 上傳到 Cloud Storage
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)

        # 讀取檔案內容
        content = await audio_file.read()

        # 上傳檔案
        blob.upload_from_string(content, content_type="audio/wav")

        audio = await AudioCrud.get(audio.id)

        if not audio:
            raise not_found

        return audio
    except Exception as e:
        # 如果上傳失敗，刪除已創建的資料庫記錄
        if audio:
            await AudioCrud.delete(audio.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.post("/normal", status_code=status.HTTP_201_CREATED)
async def create_audio(
    newAudio: AudioSchema.AudioCreate,
):
    audio = await AudioCrud.create(newAudio)
    audio = await AudioCrud.get(audio.id)

    if not audio:
        raise not_found
    return audio


@router.get(
    "/{audio_id}", response_model=AudioSchema.AudioRead, status_code=status.HTTP_200_OK
)
async def get_audio(audio_id: int):
    audio = await AudioCrud.get(audio_id)
    if audio:
        return audio

    raise not_found


@router.get(
    "", response_model=list[AudioSchema.AudioRead], status_code=status.HTTP_200_OK
)
async def get_all_audios():

    audios = await AudioCrud.get_all()
    if audios:
        return audios
    raise not_found


# 產生下載檔案的 URL
@router.get("/{audio_id}/download")
async def download_audio(audio_id: int, dir: str, file_type: str):
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{dir}/{audio_id}.{file_type}")

        # 生成簽名 URL，有效期限設為 1 小時
        url = blob.generate_signed_url(
            version="v4", expiration=3600, method="GET"  # 1 hour
        )

        return {"download_url": url}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}",
        )


# 上傳
@router.post("/{audio_id}/upload")
async def upload_audio(
    audio_id: int,
    dir: str = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
):
    try:

        file_name = f"wav/{audio_id}.wav"

        # 上傳到 Cloud Storage
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)

        # 讀取檔案內容
        content = await file.read()

        # 上傳檔案
        blob.upload_from_string(content, content_type="audio/wav")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}",
        )


@router.put("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_audio(
    updateAudio: AudioSchema.AudioUpdate, audio_id: int = Depends(check_audio_id)
):
    await AudioCrud.update(audio_id, updateAudio)

    return


@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audio(audio_id: int = Depends(check_audio_id)):
    await AudioCrud.delete(audio_id)
    return


@router.get("/db/search", response_model=List[AudioSchema.AudioRead])
async def search_audio(
    start_date: Optional[str] = Query(None, description="開始日期"),
    end_date: Optional[str] = Query(None, description="結束日期"),
    title: Optional[str] = Query(None, description="標題關鍵字"),
    info: Optional[str] = Query(None, description="描述關鍵字"),
    term: Optional[str] = Query(None, description="術語關鍵字"),
    transcript: Optional[str] = Query(None, description="逐字稿關鍵字"),
):
    try:
        audios = await AudioCrud.search(
            start_date=start_date,
            end_date=end_date,
            title=title,
            info=info,
            term=term,
            transcript=transcript,
        )
        return audios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜尋音訊檔案時發生錯誤：{str(e)}")
