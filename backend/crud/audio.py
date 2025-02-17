from sqlalchemy import select, update, delete, and_, or_, cast, Date, String
from sqlalchemy.ext.asyncio import AsyncSession
from models.audio import Audio as AudioModel
from schemas import audio as AudioSchema
from database import crud_class_decorator
from datetime import datetime


@crud_class_decorator
class AudioCrudManager:
    async def create_with_file(
        self,
        title: str,
        info: str,
        db_session: AsyncSession,
    ):
        audio = AudioModel(
            uploaded_date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            title=title,
            info=info,
            transcript={},
            term={},
        )
        db_session.add(audio)
        await db_session.commit()
        return audio

    async def create(
        self,
        newAudio: AudioSchema.AudioCreate,
        db_session: AsyncSession,
    ):
        audio_dict = newAudio.model_dump()
        audio = AudioModel(
            uploaded_date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            transcript={},
            term={},
            **audio_dict,
        )
        db_session.add(audio)
        await db_session.commit()
        return audio

    async def get(self, audio_id: int, db_session: AsyncSession):
        stmt = select(AudioModel).where(AudioModel.id == audio_id)
        result = await db_session.execute(stmt)
        audio = result.first()
        return audio[0] if audio else None

    async def get_all(self, db_session: AsyncSession):
        stmt = select(AudioModel)
        result = await db_session.execute(stmt)
        result = result.unique()
        return [audio[0] for audio in result.all()]

    async def update(
        self,
        audio_id: int,
        updateAudio: AudioSchema.AudioUpdate,
        db_session: AsyncSession,
    ):
        updateAudio_dict = updateAudio.model_dump(exclude_none=True)
        if updateAudio_dict:
            stmt = (
                update(AudioModel)
                .where(AudioModel.id == audio_id)
                .values(updateAudio_dict)
            )
            await db_session.execute(stmt)
            await db_session.commit()
        return

    async def delete(self, audio_id: int, db_session: AsyncSession):
        stmt = delete(AudioModel).where(AudioModel.id == audio_id)
        await db_session.execute(stmt)
        await db_session.commit()

        return

    async def search(
        self,
        start_date: str,
        end_date: str,
        title: str,
        info: str,
        term: str,
        transcript: str,
        db_session: AsyncSession,
    ):
        async with db_session.begin():
            query = select(AudioModel)
            date_conditions = []
            search_conditions = []

            print("Start date condition:", start_date)
            print("End date condition:", end_date)

            # 日期條件維持 AND 邏輯
            if start_date:
                date_conditions.append(
                    cast(AudioModel.uploaded_date, Date) >= start_date
                )
            if end_date:
                date_conditions.append(cast(AudioModel.uploaded_date, Date) <= end_date)

            # 搜尋條件改為 OR 邏輯
            if title:
                search_conditions.append(AudioModel.title.ilike(f"%{title}%"))
            if info:
                search_conditions.append(AudioModel.info.ilike(f"%{info}%"))
            if term:
                search_conditions.append(
                    AudioModel.term.cast(String).ilike(f"%{term}%")
                )
            if transcript:
                search_conditions.append(
                    AudioModel.transcript.cast(String).ilike(f"%{transcript}%")
                )

            # 組合條件：日期條件為 AND，搜尋條件為 OR
            if date_conditions and search_conditions:
                query = query.where(and_(*date_conditions, or_(*search_conditions)))
            elif date_conditions:
                query = query.where(and_(*date_conditions))
            elif search_conditions:
                query = query.where(or_(*search_conditions))

            result = await db_session.execute(query)
            return [row[0] for row in result.unique().all()]
