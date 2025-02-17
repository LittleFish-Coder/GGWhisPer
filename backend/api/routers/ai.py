from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
import requests
from .depends import check_audio_id

router = APIRouter(prefix="/ai", tags=["AI"])

ip = "35.192.107.93"


@router.get("/summarize/{audio_id}", status_code=status.HTTP_200_OK)
def get_summary(audio_id: int = Depends(check_audio_id)):
    response = requests.get("http://" + ip + ":8888/summarize/" + str(audio_id))
    summary = response.json()
    return summary


@router.get("/inference/{audio_id}", status_code=status.HTTP_200_OK)
def inference_audio(audio_id: int = Depends(check_audio_id)):
    response = requests.get("http://" + ip + ":8888/inference/" + str(audio_id))
    inference = response.json()
    return inference


@router.get("/transcript/{audio_id}", status_code=status.HTTP_200_OK)
def get_transcript(audio_id: int = Depends(check_audio_id)):
    response = requests.get("http://" + ip + ":8888/transcript/" + str(audio_id))
    transcript = response.json()
    return transcript


@router.get("/term/{audio_id}", status_code=status.HTTP_200_OK)
def get_term(audio_id: int = Depends(check_audio_id)):
    response = requests.get("http://" + ip + ":8888/term/" + str(audio_id))
    term = response.json()
    return term


@router.get("/chatbot", status_code=status.HTTP_200_OK)
def post_chatbot_q(query: str):
    response = requests.post("http://" + ip + ":8888/chatbot?query=" + query)
    reply = response.json()
    return reply
