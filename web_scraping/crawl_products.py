import json
import os
import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

input_file = "shl_links_with_adaptive.json"

if not os.path.exists(input_file):
    print(f"{input_file} not found. Run the link scraper first.")
    exit()

with open(input_file, "r") as f:
    ITEMS = json.load(f)


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    return driver


def extract_page_data(soup, item, index):
    # 1. Name
    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else "Unknown"

    # 2. Description
    description = ""
    h4_desc = soup.find(
        lambda tag: tag.name == "h4" and "Description" in tag.get_text()
    )
    if h4_desc:
        sib = h4_desc.find_next_sibling("p")
        if sib:
            description = sib.get_text(" ", strip=True)
        else:
            parent = h4_desc.find_parent("div")
            if parent:
                description = (
                    parent.get_text(" ", strip=True).replace("Description", "").strip()
                )

    # 3. Assessment Length + Test Type + Remote
    # A. Duration
    duration = None
    # Search entire page text for the pattern (safer than finding specific parents)
    # limit search to body content to avoid header/footer noise if needed
    body_text = soup.get_text(" ", strip=True)
    m = re.search(r"minutes\s*=\s*(\d+)", body_text, re.IGNORECASE)
    if m:
        duration = int(m.group(1))

    # B. Test Type
    test_type = []
    # Find the label "Test Type:" explicitly
    # Use BS4 string search to find the element containing this text
    tt_label = soup.find(string=re.compile("Test Type:", re.IGNORECASE))

    if tt_label:
        # The badges are usually in the same container (p or div) or a sibling
        container = tt_label.find_parent("p") or tt_label.find_parent("div")

        if container:
            # Find all badges inside this container
            type_spans = container.find_all("span", class_="product-catalogue__key")

            mapping = {
                "A": "Ability & Aptitude",
                "B": "Biodata & Situational Judgement",
                "C": "Competencies",
                "D": "Development & 360",
                "E": "Assessment Exercises",
                "K": "Knowledge & Skills",
                "P": "Personality & Behaviour",
                "S": "Simulations",
            }

            for span in type_spans:
                code = span.get_text(strip=True)
                if code in mapping:
                    test_type.append(mapping[code])
                else:
                    test_type.append(code)

    # C. Remote Support
    remote_support = "No"
    # Find label "Remote Testing:"
    rt_label = soup.find(string=re.compile("Remote Testing:", re.IGNORECASE))

    if rt_label:
        container = rt_label.find_parent("p") or rt_label.find_parent("div")
        if container:
            circle_span = container.find(
                "span", class_=lambda c: c and "catalogue__circle" in c
            )
            if circle_span:
                classes = circle_span.get("class", [])
                if "-yes" in " ".join(classes):
                    remote_support = "Yes"
                elif "-no" in " ".join(classes):
                    remote_support = "No"

    return {
        # "id": index,
        "name": name,
        "url": item["url"],
        "description": description[:3000],
        "duration": duration,
        "adaptive_support": item.get("adaptive_support", "No"),
        "remote_support": remote_support,
        "test_type": test_type,
    }


def main():
    driver = setup_driver()
    final_products = []

    print(f"Starting detailed scrape of {len(ITEMS)} products...")

    try:
        for i, item in enumerate(ITEMS):
            url = item["url"]

            # checkpoint after50
            if i > 0 and i % 50 == 0:
                print(f"Saving checkpoint at {i}...")
                with open("shl_products_final_checkpoint.json", "w") as f:
                    json.dump(final_products, f, indent=2)

            print(f"[{i + 1}/{len(ITEMS)}] Visiting: {url}")

            max_retries = 10
            success = False

            for attempt in range(max_retries):
                try:
                    driver.get(url)
                    time.sleep(1.5 + (attempt * 2))

                    soup = BeautifulSoup(driver.page_source, "html.parser")

                    page_h1 = (
                        soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
                    )
                    page_title = driver.title.lower()

                    is_error = (
                        "504" in page_title
                        or "error" in page_title
                        or "bad gateway" in page_h1.lower()
                        or "error" in page_h1.lower()
                    )

                    if is_error:
                        print(
                            f"  [Attempt {attempt + 1}] Detected Error Page ({page_title}). Retrying..."
                        )
                        continue  # Retry loop

                    product_data = extract_page_data(soup, item, i)
                    final_products.append(product_data)
                    success = True
                    break

                except Exception as e:
                    # wait before retrying
                    print(f"  [Attempt {attempt + 1}] Exception: {e}")
                    time.sleep(2)

            # after 10 attempts
            if not success:
                print(
                    f"[ERROR] Failed all {max_retries} attempts on {url}. Saving partial data."
                )
                final_products.append(item)

    finally:
        driver.quit()

    # Final Save
    print(f"Finished! Saving {len(final_products)} products to shl_products_final.json")
    with open("shl_products_final.json", "w") as f:
        json.dump(final_products, f, indent=2)


if __name__ == "__main__":
    main()
