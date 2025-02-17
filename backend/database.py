from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from contextlib import asynccontextmanager
from sqlalchemy.schema import CreateTable, DropTable
from models.audio import Audio
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 使用環境變數構建連線字串
URL_DATABASE = f"mysql+aiomysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:3306/{os.getenv('DB_NAME')}"

engine = create_async_engine(
    url=URL_DATABASE,
    echo=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autocommit=False)


@asynccontextmanager
async def get_db():
    async with SessionLocal() as db:
        yield db


async def init_db():
    async with SessionLocal() as db:
        async with db.begin():
            await db.execute(CreateTable(Audio.__table__, if_not_exists=True))


async def close_db():
    async with SessionLocal() as db:
        async with db.begin():
            await db.execute(DropTable(Audio.__table__))

    await engine.dispose()


def db_session_decorator(func):
    async def wrapper(*args, **kwargs):
        async with get_db() as db_session:
            kwargs["db_session"] = db_session
            result = await func(*args, **kwargs)
            return result

    return wrapper


def crud_class_decorator(cls):
    for name, method in cls.__dict__.items():
        if callable(method):
            setattr(cls, name, db_session_decorator(method))

    return cls
