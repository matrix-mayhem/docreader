import os
import faiss
import numpy as np
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Text, select

from google import genai

# -----------------------------
# Load Environment
# -----------------------------
load_dotenv()

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Gemini Setup
# -----------------------------
client = genai.Client(api_key=os.getenv("GOOGLE_API"))

LLM_MODEL = "gemini-2.5-flash"
EMBED_MODEL = "gemini-embedding-001"

# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI()

# -----------------------------
# Database (Async SQLite)
# -----------------------------
DATABASE_URL = "sqlite+aiosqlite:///./rag.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)
Base = declarative_base()

class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    source = Column(Text)

# -----------------------------
# Memory Store (Chat History)
# -----------------------------
memory_store: Dict[str, List[str]] = {}

def get_history(session_id: str):
    return memory_store.get(session_id, [])

def update_history(session_id: str, user, bot):
    memory_store.setdefault(session_id, []).append(f"User: {user}")
    memory_store[session_id].append(f"Bot: {bot}")

# -----------------------------
# FAISS Globals
# -----------------------------
faiss_index = None
doc_store = []

# -----------------------------
# Chunking Function
# -----------------------------
def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks

# -----------------------------
# Embedding Function
# -----------------------------
def embed_text(text):
    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text
    )
    return np.array(response.embeddings[0].values, dtype="float32")

# -----------------------------
# URL Crawler
# -----------------------------
def crawl_url(url: str):

    logger.info(f"Crawling URL: {url}")

    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    except Exception as e:
        logger.error(f"Failed to crawl {url}: {e}")
        return None

# -----------------------------
# Rebuild FAISS Index
# -----------------------------
async def rebuild_faiss():

    global faiss_index, doc_store

    logger.info("Rebuilding FAISS index...")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Knowledge))
        rows = result.scalars().all()

    doc_store = [row.content for row in rows]

    if not doc_store:
        faiss_index = None
        return

    embeddings = np.array([embed_text(doc) for doc in doc_store])
    dimension = embeddings.shape[1]

    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings)

# -----------------------------
# Retrieval
# -----------------------------
def retrieve_docs(query, k=3):

    if faiss_index is None:
        return []

    query_vector = embed_text(query)
    D, I = faiss_index.search(np.array([query_vector]), k)

    return [doc_store[i] for i in I[0]]

# -----------------------------
# Confidence Score
# -----------------------------
def confidence_score(answer):
    if "I don't know" in answer:
        return 0.2
    return 0.9

# -----------------------------
# Startup Event
# -----------------------------
@app.on_event("startup")
async def startup():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:

        result = await db.execute(select(Knowledge))
        if not result.scalars().all():

            # Seed internal knowledge
            db.add_all([
                Knowledge(content="Employees get 20 annual leave days.", source="policy"),
                Knowledge(content="Unused leave expires after one year.", source="policy")
            ])

            urls = [
                "https://example.com",
                "https://www.wikipedia.org",
                "https://www.bombayshavingcompany.com/blogs/trimmer-blog/5-things-to-check-before-buying-a-trimmer"
            ]

            for url in urls:
                text = crawl_url(url)
                if text:
                    chunks = chunk_text(text)

                    for chunk in chunks:
                        db.add(Knowledge(content=chunk, source=url))

            await db.commit()

    await rebuild_faiss()

# -----------------------------
# Schemas
# -----------------------------
class ChatRequest(BaseModel):
    session_id: str
    question: str

class KnowledgeCreate(BaseModel):
    content: str
    source: str

class URLIngest(BaseModel):
    url: str

# =====================================================
# 🚀 CHATBOT ENDPOINT
# =====================================================
@app.post("/chat")
async def chat(req: ChatRequest):

    history = "\n".join(get_history(req.session_id))
    retrieved_docs = retrieve_docs(req.question)

    context = "\n".join(retrieved_docs)

    prompt = f"""
You are an enterprise assistant.

Chat History:
{history}

Context:
{context}

Question:
{req.question}

If answer not found, say: I don't know.
"""

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt
    )

    answer = response.text

    update_history(req.session_id, req.question, answer)

    return {
        "answer": answer,
        "confidence": confidence_score(answer),
        "sources": retrieved_docs
    }

# =====================================================
# 🚀 CRUD KNOWLEDGE
# =====================================================
@app.post("/knowledge")
async def add_knowledge(data: KnowledgeCreate):

    async with AsyncSessionLocal() as db:
        db.add(Knowledge(content=data.content, source=data.source))
        await db.commit()

    await rebuild_faiss()
    return {"message": "Knowledge added"}

@app.get("/knowledge")
async def list_knowledge():

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Knowledge))
        return result.scalars().all()

@app.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: int):

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Knowledge).where(Knowledge.id == knowledge_id))
        row = result.scalar_one_or_none()

        if not row:
            raise HTTPException(404, "Knowledge not found")

        await db.delete(row)
        await db.commit()

    await rebuild_faiss()
    return {"message": "Knowledge deleted"}

# =====================================================
# 🚀 URL INGESTION
# =====================================================
@app.post("/ingest-url")
async def ingest_url(data: URLIngest):

    text = crawl_url(data.url)

    if not text:
        raise HTTPException(400, "Failed to crawl URL")

    chunks = chunk_text(text)

    async with AsyncSessionLocal() as db:
        for chunk in chunks:
            db.add(Knowledge(content=chunk, source=data.url))
        await db.commit()

    await rebuild_faiss()

    return {
        "message": "URL ingested",
        "chunks_stored": len(chunks)
    }