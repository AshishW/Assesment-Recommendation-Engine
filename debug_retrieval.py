import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)  # all-MiniLM-L6-v2
vector_db = FAISS.load_local(
    "shl_faiss_index", embeddings, allow_dangerous_deserialization=True
)


def get_ground_truth():
    df = pd.read_csv("train_set.csv")

    query_col = df.columns[0]
    url_col = df.columns[1]

    ground_truth = {}
    for _, row in df.iterrows():
        query = str(row[query_col])
        url = str(row[url_col])
        if query not in ground_truth:
            ground_truth[query] = set()
        ground_truth[query].add(url)
    return ground_truth


# ground_truth = get_ground_truth()

# query = "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."  # Replace with a REAL query from your CSV that failed
# query = "I want to hire new graduates for a sales role in my company, the budget is for about an hour for each test. Give me some options"
query = """
Marketing Manager, B2B marketing, marketing strategy, brand positioning, community building, demand generation, events, social media, content strategy, developer community, partnerships
"""
# correct_url_part = "automata-fix-new"
# correct_url_part = "entry-level-sales-7-1"
correct_url_part = "manual-testing-new"


docs = vector_db.similarity_search(query, k=20)

print(f"Query: {query}")
print(f"Looking for: {correct_url_part}")
print("-" * 30)

found_at = -1
for i, d in enumerate(docs):
    print(f"Rank {i + 1}: {d.metadata['name']} | {d.metadata['url']}")
    if correct_url_part in d.metadata["url"]:
        found_at = i + 1

print("-" * 30)
if found_at != -1:
    print(f"SUCCESS: Found at Rank {found_at}")
else:
    print("FAILURE: Not in Top 20")
