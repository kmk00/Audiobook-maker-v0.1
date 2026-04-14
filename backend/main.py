from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from db.database import Base, engine

from db import models
from api import characters, tts

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["http://localhost:5173", "tauri://localhost"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory="audiobooks/audio"), name="audio")

app.include_router(characters.router)
app.include_router(tts.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}