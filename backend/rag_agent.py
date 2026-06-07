import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph , END
from langgraph.checkpoint.memory import MemorySaver
from qdrant_client import QdrantClient
from qdrant_client.models import Filter,FieldCondition,MatchValue
from embedder import embed_query
from typing import TypedDict , Annotated
import operator

load_dotenv()

COLLECTION_NAME = "video_chunks"
TOP_K = 5
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")


if qdrant_url and qdrant_api_key:
    qdrant = QdrantClient(url=qdrant_url,api_key=qdrant_api_key)
else:
    qdrant = QdrantClient(host="localhost",port=6333)

llm = ChatGroq(
    model = "llama-3.3-70b-versatile",
    api_key = os.getenv("GROQ_API_KEY"),
    temperature = 0.3,
    streaming = True,
)

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    context:str
    sources:list

# it will embed query , search qdrant and return context string + sources list 
def retrieve(query:str,video_label:str=None)->tuple[str,list]:
    query_vector = embed_query(query)

    labels_to_fetch = (
        [video_label] if video_label
        else ["A", "B"]  
    )

    context_parts = []
    sources = []

    for label in labels_to_fetch:
        response = qdrant.query_points(
            collection_name = COLLECTION_NAME,
            query = query_vector,
            limit = TOP_K,
            query_filter = Filter(
                must = [
                    FieldCondition(
                        key = "video_label",
                        match = MatchValue(value=label)
                    )
                ]
            ),
            with_payload = True,
        )
        
        for i, hit in enumerate(response.points):
            p = hit.payload
            lbl = p.get("video_label", label)
            chunk_idx = p.get("chunk_index", i)
            text = p.get("text", "")
            title = p.get("title", "Unknown")
            creator = p.get("creator", "Unknown")
            engagement = p.get("engagement_rate", 0)
            views = p.get("views", 0)
            likes = p.get("likes", 0)
            comments = p.get("comments", 0)

            context_parts.append(
                f"[Source: Video {lbl},Chunk {chunk_idx}]\n"
                f"Title: {title}\n"
                f"Creator: {creator}\n"
                f"Views: {views} | Likes: {likes} | Comments: {comments} | Engagement: {engagement}%\n"
                f"Content: {text}\n"
            )
            sources.append({
                "video_id": lbl,
                "chunk_index": chunk_idx,
                "title": title,
                "score": round(hit.score, 4),
                "text_preview": text[:100] + "..." if len(text) > 100 else text,
            })

    if not context_parts:
        return "No relevant content found", []

    return "\n\n".join(context_parts), sources

# it will detech if user is askinf about a specific video to filter retrieval
def detect_video_filter(query:str)->str|None:
    q = query.lower()
    only_a = "video a" in q and "video b" not in q
    only_b = "video b" in q and "video a" not in q
    if only_a:
        return "A"
    if only_b:
        return "B"
    return None


SYSTEM_PROMPT = """
You are an expert social media analytics assistant helping creators understand their video performance.

You have retrieval access to TWO videos:
- Video A: YouTube video
- Video B: Instagram Reel

IMPORTANT RULES:
1. Engagement rate, views, likes, and comments are in EVERY chunk's metadata header — always read them
2. ALWAYS cite sources as [Video A, Chunk N] or [Video B, Chunk N]
3. NEVER say data is unavailable if it appears in the context headers below
4. When comparing, explicitly state both videos' numbers side by side
5. Base improvement suggestions on actual transcript content

Context retrieved from video database:
{context}
"""

# it will retrieve relevant chunks based on latest user message.
def retrieval_node(state:AgentState)-> AgentState:
    last_message = state["messages"][-1].content
    video_filter = detect_video_filter(last_message)
    context,sources = retrieve(last_message,video_label=video_filter)
    return {
        "messages":[],
        "context":context,
        "sources":sources,
    }

# it will generate response using retrieved context + conversation history
def generation_node(state:AgentState)->AgentState:
    context = state.get("context","")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm
    response = chain.invoke({"messages":state["messages"]})

    return {
        "messages":[AIMessage(content=response.content)],
        "context":context,
        "sources":state.get("sources",[]),
    }

# it will build the graph
def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve",retrieval_node)
    workflow.add_node("generate",generation_node)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve","generate")
    workflow.add_edge("generate",END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


graph = build_graph()
print("[RAG] LangGraph Agent prepared")

# it will return the full resposne + sources used for testing
def chat(query:str,thread_id:str="default")->dict:
    config = {"configurable":{"thread_id":thread_id}}
    result = graph.invoke(
        {
            "messages":[HumanMessage(content=query)],
            "context": "",
            "sources":[],
        },
        config=config
    )
    return {
        "answer": result["messages"][-1].content,
        "sources":result.get("sources",[]),
    }

# it will generate streaming responses token by token (async)
async def chat_stream(query:str,thread_id:str="default"):
    config = {"configurable":{"thread_id":thread_id}}

    async for event in graph.astream_events(
        {
            "messages":[HumanMessage(content=query)],
            "context":"",
            "sources":[],
        },
        config=config,
        version="v2",
    ):
        kind = event.get("event","")
        if kind == "on_chat_model_stream":
            chunk = event.get("data",{}).get("chunk",None)
            if chunk and hasattr(chunk,"content") and chunk.content:
                yield chunk.content

    