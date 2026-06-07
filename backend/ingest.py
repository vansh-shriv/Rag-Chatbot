import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue
)
from extractors.youtube import extract_youtube
from extractors.instagram import extract_instagram

load_dotenv()

COLLECTION_NAME = "video_chunks"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

print("[Ingest] Loading embedding model")
embedder = SentenceTransformer(EMBEDDING_MODEL)
VECTOR_DIM = embedder.get_sentence_embedding_dimension()
if qdrant_url and qdrant_api_key:
    qdrant = QdrantClient(url=qdrant_url,api_key=qdrant_api_key)
else:
    qdrant = QdrantClient(host="localhost",port=6333)

# it will create qdrant collection if it doesnt exist
def ensure_collection():
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in existing:
        qdrant.create_collection(
            collection_name = COLLECTION_NAME,
            vectors_config=VectorParams(
                size = VECTOR_DIM,
                distance = Distance.COSINE
            )
        )
        print(f"[Ingest] Created Qdrant collection '{COLLECTION_NAME}'")
    else:
        print(f"[Ingest] Using existing Qdrant collection '{COLLECTION_NAME}'")

# it will delete existing chunks for a video label before re-ingesting
def clear_video_chunks(video_label: str):
    qdrant.delete(
        collection_name = COLLECTION_NAME,
        points_selector = Filter(
            must = [
                FieldCondition(
                    key="video_label",
                    match=MatchValue(value=video_label)
                )
            ]
        )
    )
    print(f"[Ingest] Cleared old chunks for Video {video_label}")

# it will split transcript into overlapping chunks
def chunk_transcript(transcript_text:str,video_label:str,metadata:dict)->list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP,
        separators=["\n\n","\n","."," ",""]
    )
    chunks = splitter.split_text(transcript_text)
    print(f"[Ingest] Video {video_label}: {len(chunks)} chunks from transcript")

    result = []

    for i,chunk in enumerate(chunks):
        result.append({
            "chunk_index":i,
            "text":chunk,
            "video_label":video_label,
            "metadata":metadata,
        })
    return result

# it will embed each chunk and upsert into Qdrant with full metadata payload
def embed_and_store(chunks:list[dict]):
    if not chunks:
        print("[Ingest] No chunks to embed")
        return
    
    texts = [c["text"] for c in chunks]

    print(f"[Ingest] Embedding {len(texts)} chunks")
    vectors = embedder.encode(
        texts,
        batch_size = 32,
        show_progress_bar = True,
        normalize_embeddings=True
    )

    points = []
    for i, (chunk,vector) in enumerate(zip(chunks,vectors)):
        payload = {
             "text": chunk["text"],
            "chunk_index": chunk["chunk_index"],
            "video_label": chunk["video_label"],
            "title": chunk["metadata"].get("title", ""),
            "creator": chunk["metadata"].get("creator", ""),
            "views": chunk["metadata"].get("views", 0),
            "likes": chunk["metadata"].get("likes", 0),
            "comments": chunk["metadata"].get("comments", 0),
            "engagement_rate": chunk["metadata"].get("engagement_rate", 0),
            "duration": chunk["metadata"].get("duration", 0),
            "upload_date": chunk["metadata"].get("upload_date", ""),
            "hashtags": chunk["metadata"].get("hashtags", []),
            "source": chunk["metadata"].get("source", ""),
            "url": chunk["metadata"].get("url", "")
        }
        points.append(
            PointStruct(
                id = abs(hash(f"{chunk['video_label']}_{chunk['chunk_index']}")),
                vector=vector.tolist(),
                payload=payload
            )
        )

    qdrant.upsert(collection_name=COLLECTION_NAME,points=points)
    print(f"[Ingest] Stored {len(points)} points in Qdrant")

# Master ingestion fucntion
def ingest_videos(youtube_url:str,instagram_url:str)->dict:
    ensure_collection()
    print("\n[Ingest] Extracting Youtube Video")
    video_a = extract_youtube(youtube_url)
    print("\n[Ingest] Extracting Instagram Video")
    video_b = extract_instagram(instagram_url)

    for video in [video_a,video_b]:
        label = video["video_id"]

        video["metadata"]["source"] = video["source"]
        video["metadata"]["url"] = video["url"]

        clear_video_chunks(label)
        chunks = chunk_transcript(
            video["transcript_text"],
            label,
            video["metadata"]
        )
        embed_and_store(chunks)
    
    print("\n[Ingest] Completed")

    return {
        "video_a":{
            "label": "A",
            "source":"youtube",
            "url":youtube_url,
            "metadata":video_a["metadata"],
            "chunks_stored":len(video_a["transcript_text"]),
        },
        "video_b":{
            "label": "B",
            "source":"instagram",
            "url":instagram_url,
            "metadata":video_b["metadata"],
            "chunks_stored":len(video_b["transcript_text"]),
        }
    }




