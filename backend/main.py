from database import init_db, close_db
from api.api import api_run
from asyncio import run


async def main():
    await init_db()
    await api_run()
    await close_db()


if __name__ == "__main__":
    run(main=main())
