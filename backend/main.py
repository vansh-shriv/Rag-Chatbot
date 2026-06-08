import os
import json
import uuid
from fastapi import FastAPI , HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from ingest import ingest_videos
from rag_agent import chat_stream,graph

load_dotenv()

app = FastAPI(title="Video RAG Chatbot API")

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in allowed_origins if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    youtube_url:str
    instagram_url:str

class ChatRequest(BaseModel):
    query:str
    thread_id:str="default"

video_metadata_store = {}


@app.get("/")
def root():
    return {"status":"Video RAG Api is running"}

@app.post("/ingest")
async def ingest(request:IngestRequest):
    try:
        print(f"\n[API] Ingesting Videos")
        print(f"[API] YouTube: {request.youtube_url}")
        print(f"[API] Instagram: {request.instagram_url}")

        result = ingest_videos(request.youtube_url,request.instagram_url)

        video_metadata_store["A"]=result["video_a"]["metadata"]
        video_metadata_store["B"]=result["video_b"]["metadata"]

        return {
            "success" :True,
            "video_a":result["video_a"],
            "video_b":result["video_b"],
        }

    except Exception as e:
        print(f"[API] Ingest Error: {str(e)}")
        raise HTTPException(status_code=500,detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    async def event_generator():
        sources = []
        full_response = ""

        try:
            async for token in chat_stream(request.query,request.thread_id):
                full_response += token
                yield{
                    "event":"token",
                    "data":json.dumps({"token":token})
                }
            config = {"configurable":{"thread_id":request.thread_id}}
            state = graph.get_state(config)
            if state and state.values:
                sources = state.values.get("sources",[])

            yield {
                "event":"sources",
                "data":json.dumps({"sources":sources})
            }

            yield {
                "event":"done",
                "data":json.dumps({"done":True})
            }
        
        except Exception as e:
            print(f"[API] Chat Stream Error: {str(e)}")
            yield{
                "event":"error",
                "data":json.dumps({"error":str(e)})
            }
    
    return EventSourceResponse(event_generator())

@app.get("/metadata")
def get_metadata():
    if not video_metadata_store:
        raise HTTPException(status_code = 404,detail = "No vides ingested yet")
    return {
        "video_a":video_metadata_store.get("A",{}),
        "video_b":video_metadata_store.get("B",{}),
    }

@app.get("/health")
def health():
    return {"status":"ok"}
