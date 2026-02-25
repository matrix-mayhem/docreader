from google import genai
from fastapi import FastAPI
import os
from dotenv import load_dotenv
import faiss
import numpy as np

#User → FastAPI → LangChain RAG Chain → Retriever (FAISS) → LLM → Response
load_dotenv()

app = FastAPI()

# Initialize the new Google Gen AI Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Load docs
with open("rag/docs.txt") as f:
    # .read().splitlines() removes the \n characters automatically
    docs = f.read().splitlines()

# Create embeddings
embeddings = []
print("Creating embeddings using gemini-embedding-001...")
for doc in docs:
    if not doc.strip(): continue
    
    # Corrected Model: gemini-embedding-001
    res = client.models.embed_content(
        model="gemini-embedding-001",
        contents=doc,
        config={'task_type': 'RETRIEVAL_DOCUMENT'}
    )
    # Corrected result path: .embeddings[0].values
    embeddings.append(res.embeddings[0].values)

# Convert to FAISS index
embeddings_array = np.array(embeddings, dtype="float32")
dimension = embeddings_array.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings_array)

#multi doc retrieval
def retrieve(query, k=3):
    q_emb = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    D, I = index.search(np.array([q_emb], dtype="float32"), k=k)

    results = [docs[i] for i in I[0]]
    return results

def retrieve(query):
    res = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config={'task_type': 'RETRIEVAL_QUERY'}
    )
    q_emb = np.array([res.embeddings[0].values], dtype="float32")
    
    D, I = index.search(q_emb, k=1)
    return docs[I[0][0]]

def ask_llm(question, context):
    # The SDK uses 'system_instruction' for rules and 'contents' for the prompt
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config={
            'system_instruction': "Answer ONLY using provided context. If not found, say you don't know."
        },
        contents=f"Context: {context}\n\nQuestion: {question}"
    )
    return response.text

# ---- API endpoint ----
# @app.post("/ask")
# def ask_question(req: QueryRequest):
#     contexts = retrieve(req.question, k=3)
#     answer = ask_llm(req.question, contexts)

#     return {
#         "question": req.question,
#         "retrieved_context": contexts,
#         "answer": answer
#     }

# --- Example Run ---
while(True):
    query = input("Me:")
    context = retrieve(query)
    answer = ask_llm(query, context)
    print(f"Yulubot: {answer}")