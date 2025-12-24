# SHL Assessment Recommendation System

## Project Overview

An intelligent **Retrieval-Augmented Generation (RAG)** system that recommends relevant HR assessments from SHL's product catalog based on job descriptions and hiring requirements. The system uses web scraping to collect assessment data, vector embeddings for semantic search, and AI-powered ranking to provide personalized assessment recommendations.

### Key Features

- **Web Scraping**: Automated crawling of SHL's product catalog with retry logic and error handling
- **Vector Search**: FAISS-based semantic search using sentence transformers
- **AI-Powered Recommendations**: Google Generative AI (Gemini) for intelligent assessment matching
- **Evaluation Metrics**: Recall@k measurement against ground truth training data
- **FastAPI Backend**: RESTful API for assessment recommendations
- **RAG Pipeline**: Context-aware retrieval and generation

---


### File Descriptions

| File | Purpose |
|------|---------|
| **main.py** | FastAPI server with `/recommend` endpoint and RAG chain |
| **vector_db.py** | Creates FAISS vector database from documents |
| **rag_data.py** | Loads and formats SHL product data into LangChain documents |
| **evaluate.py** | Calculates Recall@k against ground truth queries |
| **debug_retrieval.py** | Tests and debugs retrieval quality |
| **web_scraping/crawl_urls_metadata.py** | Scrapes product URLs and adaptive support info |
| **web_scraping/crawl_products.py** | Scrapes detailed product information (name, description, test types, etc.) |

---

## Local Setup Instructions

### Prerequisites

- **Python 3.9+**
- **Google Chrome** (for Selenium)
- **API Keys**: Google Generative AI, Hugging Face

### Clone & Install Dependencies

```bash
cd c:\My Drive\SHL_ASSESMENT
pip install -r requirements.txt
```

### Set up Env variables:
```
GOOGLE_API_KEY=your_google_gemini_api_key
HF_TOKEN=your_huggingface_token
```

### web scraping(optional - Data already included)
```
# Step 1: Scrape URLs and metadata
python web_scraping/crawl_urls_metadata.py
# Output: shl_links_with_adaptive.json

# Step 2: Scrape detailed product information
python web_scraping/crawl_products.py
# Output: shl_products_final.json
⚠️ Note: Scraping takes time. The final data is already included in the repo.
```

## API Endpoints:

1. "http:localhost:8000/recommend" - To get recommendations

    request:
    ```json
    {
        "query": "I need an assessment for a Marketing Manager role focusing on strategy and leadership"
    }
    ```

    response:
    ```json
    {
    "recommended_assessments": [
        {
            "url": "https://www.shl.com/solutions/products/...",
            "name": "Leadership Assessment",
            "adaptive_support": "Yes",
            "description": "Measures leadership competencies...",
            "duration": 45,
            "remote_support": "Yes",
            "test_type": ["Competencies", "Development & 360"]
        },
        
    ]
    }
    ```
2. "http:localhost:8000/health" - Health check endpoint

## Performance metrics
Recall@10 = (correct recommendations in top 10) / (total relevant assessments)

## Attribution

This project scrapes and indexes data from *SHL.com*.