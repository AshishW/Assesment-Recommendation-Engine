import json
import os

from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()


def load_shl_data():
    with open("./web_scraping/shl_products_final.json", "r") as f:
        data = json.load(f)

    documents = []

    for item in data:
        # Context ENg
        page_content = f"""
        Assessment Name: {item["name"]}
        Test Types: {", ".join(item["test_type"])}
        Description: {item["description"]}
        Duration: {item["duration"]} minutes
        remote_support: {item["remote_support"]}
        """

        meta_data = {
            "url": item["url"],
            "name": item["name"],
            "adaptive_support": item["adaptive_support"],
            "description": item["description"],
            "duration": item["duration"],
            "remote_support": item["remote_support"],
            "test_type": item["test_type"],
        }

        doc = Document(page_content=page_content, metadata=meta_data)
        documents.append(doc)
    print(f"Processed {len(documents)} docs.")
    return documents


if __name__ == "__main__":
    docs = load_shl_data()
    print(f"sample Document Content: \n{docs[0].page_content}")
    print(f"sample metadata: \n{docs[0].metadata}")
