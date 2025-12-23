import json
import os
from typing import List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate

# from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field

# from sentence_transformers import CrossEncoder

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
# reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
HF_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-mpnet-base-v2/pipeline/feature-extraction"

HF_TOKEN = os.environ.get("HF_TOKEN")

if HF_TOKEN is None:
    raise RuntimeError("HF_TOKEN environment variable not set")

HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}


def embed_query(text: str) -> List[float]:
    resp = requests.post(
        HF_API_URL,
        headers=HF_HEADERS,
        json={"inputs": text},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data[0], list):
        return data[0]
    return data


TOP_K = 20
try:
    vector_db = FAISS.load_local(
        "shl_faiss_index", embeddings=None, allow_dangerous_deserialization=True
    )
    # retriever = vector_db.as_retriever(search_kwargs={"k": top_k})
except Exception as e:
    print(f"could not load vector_db. {e}")


def get_candidates(query_text: str):
    if vector_db is None:
        return []
    vec = embed_query(query_text)
    # search by vector instead of by text
    return vector_db.similarity_search_by_vector(vec, k=TOP_K)


class AssessmentRecommendation(BaseModel):
    url: str = Field(description="URL of the assessment")
    name: str = Field(description="Name of the assessment")
    adaptive_support: str = Field(description="'Yes' or 'No'")
    duration: Optional[int] = Field(
        description="Duration in minutes (or N/A if unknown)"
    )
    description: str = Field(description="Brief description of the assessment")
    remote_support: str = Field(description="'Yes' or 'No'")
    test_type: List[str] = Field(
        description="List of test types (e.g. ['Knowledge', 'Ability'])"
    )


class RecommendationResponse(BaseModel):
    recommended_assessments: List[AssessmentRecommendation]


model = "gemini-2.5-flash"
llm = ChatGoogleGenerativeAI(model=model)
structured_llm = llm.with_structured_output(RecommendationResponse)

template = """
You are an expert HR Recruitment consultant.
Your task is to recommend top 10 relevant assessments from the provided context based on user's job description/query.

CONTEXT:
{context}

USER REQUEST:
{question}

INSTRUCTIONS:
1. Return valid JSON. key: "recommended_assessments" (list).
2. Fields: url, name, adaptive_support, description, duration, remote_support, test_type
3. select top 10 relevant matches based on the query.
"""

prompt = ChatPromptTemplate.from_template(template)


def format_docs(docs):
    # metadata in context
    context = ""
    for d in docs:
        context += f"URL: {d.metadata['url']}\n"
        context += f"Name: {d.metadata['name']}\n"
        context += f"Adaptive_support: {d.metadata['adaptive_support']}\n"
        context += f"description: {d.metadata['description']}\n"
        context += f"duration: {d.metadata['duration']}\n"
        context += f"remote_support: {d.metadata['remote_support']}\n"
        context += f"test_type: {d.metadata['test_type']}\n\n"
        # todo: consider adding the two new fields as well
    return context


def process_query(query):
    print("Processing query...\n")
    messages = [
        (
            "system",
            """
            You are helping to search a catalog of assessments.

            Given a job description or search query, output a short, comma-separated list
            of the most important keywords for matching assessments.

            Include:
            - job title or role (senior, graduate, manager, etc.)
            - core technical skills (Java, .NET, Python, SQL, Sales, etc.)
            - domain if relevant (finance, healthcare, retail)
            - soft skill words only if they are clearly primary (e.g. "sales", "customer service")
            - Other relevant important information from the query.

            Do NOT include explanation text or labels like "role:", "skills required:", etc.
            Just output comma-separated keywords along with short 2 line description of the query, for example:
            "senior backend developer, java, microservices, spring, sql, 40 minute, etc" followed by small description.
            """,
        ),
        ("human", query),
    ]

    response = llm.invoke(messages)
    print(f"Processed Query: {response.text}")
    return response.text


def retrieval_node(q: str):
    candidates = get_candidates(q)
    context = format_docs(candidates)
    return {"context": context, "question": q}


rag_chain = retrieval_node | prompt | structured_llm


class QueryRequest(BaseModel):
    query: str


@app.post("/recommend")
async def recommend_assesments(request: QueryRequest):
    try:
        query = request.query
        processed_query = process_query(query)
        # response = rag_chain.invoke(
        #     {"retrieval_query": processed_query, "llm_query": query}
        # )
        response = rag_chain.invoke(processed_query)
        result = response.dict()

        for item in result["recommended_assessments"]:
            original_url = item["url"]
            if "shl.com/products/" in original_url:
                # normalizing Urls
                item["url"] = original_url.replace(
                    "shl.com/products/", "shl.com/solutions/products/"
                )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "active"}
