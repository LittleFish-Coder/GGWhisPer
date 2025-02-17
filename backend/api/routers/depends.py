from fastapi import HTTPException, status

from crud.audio import AudioCrudManager


AudioCrud = AudioCrudManager()


async def check_audio_id(audio_id: int):
    audio = await AudioCrud.get(audio_id)
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audio does not exist"
        )

    return audio_id
