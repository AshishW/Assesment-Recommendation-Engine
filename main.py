import json
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

try:
    top_k = 10
    vector_db = FAISS.load_local(
        "shl_faiss_index", embeddings, allow_dangerous_deserialization=True
    )
    retriever = vector_db.as_retriever(search_kwargs={"k": top_k})
except Exception as e:
    print(f"could not load vector_db. {e}")


class AssessmentRecommendation(BaseModel):
    url: str = Field(description="URL of the assessment")
    name: str = Field(description="Name of the assessment")
    adaptive_support: str = Field(description="'Yes' or 'No'")
    duration: Optional[int] = Field(description="Duration in minutes (or 0 if unknown)")
    description: str = Field(description="Brief description of the assessment")
    remote_support: str = Field(description="'Yes' or 'No'")
    test_type: List[str] = Field(
        description="List of test types (e.g. ['Knowledge', 'Ability'])"
    )


class RecommendationResponse(BaseModel):
    recommended_assessments: List[AssessmentRecommendation]


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
structured_llm = llm.with_structured_output(RecommendationResponse)

template = """
You are an expert HR Recruitment consultant.
Your task is to recommend min 5 assessments from the provided context based on user's job description/query.

CONTEXT:
{context}

USER REQUEST:
{question}

INSTRUCTIONS:
1. Return valid JSON. key: "recommended_assessments" (list).
2. Fields: url, name, adaptive_support, description, duration, remote_support, test_type
3. select minimum 5, maximum 10 top matches.
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
    return context


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | structured_llm
)


class QueryRequest(BaseModel):
    query: str


@app.post("/recommend")
async def recommend_assesments(request: QueryRequest):
    try:
        response = rag_chain.invoke(request.query)
        result = response.dict()

        for item in result["recommended_assessments"]:
            original_url = item["url"]
            if "shl.com/products/" in original_url:
                # normalizing urls
                item["url"] = original_url.replace(
                    "shl.com/products/", "shl.com/solutions/products/"
                )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "active"}
