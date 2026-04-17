from contextlib import asynccontextmanager
import os
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from db.database import Base, engine

from db import models
from api import characters, tts

Base.metadata.create_all(bind=engine)

TEMP_AUDIO_DIR = "audiobooks/audio/temp"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Cleaning up temporary audio directory on startup ...")
    
    
    if os.path.exists(TEMP_AUDIO_DIR):
        shutil.rmtree(TEMP_AUDIO_DIR, ignore_errors=True)
        
    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
    
    yield
    
    print("Cleaning up temporary audio directory on shutdown ...")
    if os.path.exists(TEMP_AUDIO_DIR):
        shutil.rmtree(TEMP_AUDIO_DIR, ignore_errors=True)
    

app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:5173", "tauri://localhost","http://localhost:1420"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory="audiobooks/audio"), name="audio")
app.mount("/static_characters", StaticFiles(directory="characters"), name="static_characters")

app.include_router(characters.router)
app.include_router(tts.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}