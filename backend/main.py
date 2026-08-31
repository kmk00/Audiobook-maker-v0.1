from contextlib import asynccontextmanager
import os
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from db.database import Base, engine

from db import models
from api import characters, tts, audiobook_utils
from utils.lifespan_utils import clear_temp_directory
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Cleaning up temporary audio directory on startup ...")
    clear_temp_directory()
    
    yield
    
    print("Cleaning up temporary audio directory on shutdown ...")
    clear_temp_directory()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory="audiobooks/audio"), name="audio")
app.mount("/static_characters", StaticFiles(directory="characters"), name="static_characters")
app.mount("/output", StaticFiles(directory="audiobooks/output"), name="output")
app.mount("/timelines", StaticFiles(directory="audiobooks/timelines"), name="timelines")

app.include_router(characters.router)
app.include_router(tts.router)
app.include_router(audiobook_utils.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}