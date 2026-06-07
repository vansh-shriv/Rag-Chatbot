import os
import cohere
from dotenv import load_dotenv

load_dotenv()

COHERE_MODEL = "embed-english-light-v3.0"
VECTOR_DIM   = 384

client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))


def embed_texts(texts: list[str], input_type: str = "search_document") -> list[list[float]]:
    response = client.embed(
        texts=texts,
        model=COHERE_MODEL,
        input_type=input_type,
    )
    return response.embeddings


def embed_query(query: str) -> list[float]:
    return embed_texts([query], input_type="search_query")[0]


def embed_documents(texts: list[str]) -> list[list[float]]:
    all_embeddings = []
    batch_size = 96

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = embed_texts(batch, input_type="search_document")
        all_embeddings.extend(embeddings)
        print(f"[Embedder] Embedded {min(i + batch_size, len(texts))}/{len(texts)} chunks")

    return all_embeddings