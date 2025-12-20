import os

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from rag_data import load_shl_data


def create_vector_db(documents):
    print("creating embeddigns...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_db = FAISS.from_documents(documents, embeddings)

    vector_db.save_local("shl_faiss_index")
    print("vector db saved: 'shl_faiss_index' folder")


if __name__ == "__main__":
    docs = load_shl_data()
    create_vector_db(docs)
