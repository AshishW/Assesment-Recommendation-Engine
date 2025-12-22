import time

import pandas as pd
import requests

api_url = "http://127.0.0.1:8000/recommend"
k = 10


def get_ground_truth():
    # train set data
    df = pd.read_csv("train_set.csv")

    query_col = df.columns[0]
    url_col = df.columns[1]

    ground_truth = {}

    for _, row in df.iterrows():
        query = str(row[query_col]).strip()
        url = str(row[url_col]).strip()

        if query not in ground_truth:
            ground_truth[query] = set()
        ground_truth[query].add(url)

    return ground_truth


def calculate_recall(predicted_urls, true_urls, k=10):
    # Recall@k

    top_k_predictions = set(predicted_urls[:k])
    correct_finds = top_k_predictions.intersection(true_urls)

    if len(true_urls) == 0:
        return 0.0
    return len(correct_finds) / len(true_urls)


def main():
    ground_truths = get_ground_truth()
    print(f"found {len(ground_truths)} test queries \n")

    total_recall = 0.0

    for i, (query, true_urls) in enumerate(ground_truths.items()):
        print(f"{i + 1}/{len(ground_truths)} Query: {query} \n")

        try:
            response = requests.post(api_url, json={"query": query})

            if response.status_code == 200:
                results = response.json()

                recommendations = results.get("recommended_assessments", [])
                predicted_urls = []
                for r in recommendations:
                    predicted_urls.append(r.get("url", "").strip())
                print(f"Predicted URLS: {predicted_urls}")
                score = calculate_recall(predicted_urls, true_urls, k)
                print(f"- got {len(predicted_urls)} predictions")
                print(f" - Recall@{k}: {score: .2f}")

                total_recall += score
            else:
                print(f"API error: {response.status_code}")

        except Exception as e:
            print(f"Error Connection failed: {e}")

        time.sleep(1)

    if len(ground_truths) > 0:
        mean_recall = total_recall / len(ground_truths)
        print(f"MEAN RECALL@{k}: {mean_recall:.4f}")
    else:
        print("No query found.")


if __name__ == "__main__":
    main()
