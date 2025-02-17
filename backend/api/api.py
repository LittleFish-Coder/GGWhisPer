from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server
from .routers.audio import router as audio_router
from .routers.ai import router as summary_router

app = FastAPI()
app.include_router(audio_router)
app.include_router(summary_router)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def api_run():
    config = Config(app=app, host="0.0.0.0", port=8080)
    server = Server(config=config)

    await server.serve()

    server.run()
