import json
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.shl.com/products/product-catalog/?start={}&type=1"


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    driver.maximize_window()
    return driver


def get_links_with_adaptive_info():
    driver = setup_driver()
    all_products_map = {}
    start = 0
    batch_size = 12

    print("Starting Crawl...")

    try:
        print("Loading homepage, clear cookies...")
        driver.get("https://www.shl.com/products/product-catalog/")
        time.sleep(5)

        try:
            print("Attempting to close cookie banner...")
            accept_btn = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            accept_btn.click()
            print("Closed via ID.")
            time.sleep(1)
        except:
            try:
                accept_btn = driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Accept')]"
                )
                accept_btn.click()
                print("Closed via Text.")
            except:
                print("No cookie banner found or could not close (continuing).")

        while True:
            url = BASE_URL.format(start)
            print(f"Navigating to: {url}")
            driver.get(url)

            print("Waiting for table rows...")
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[contains(@href, '/view/')]")
                    )
                )
                print("Page loaded.")
            except:
                print("Timeout waiting for content. Page might be empty or blocked.")

            soup = BeautifulSoup(driver.page_source, "html.parser")

            links = soup.find_all("a", href=True)
            new_found_count = 0

            product_links = [a for a in links if "product-catalog/view/" in a["href"]]

            for a in product_links:
                full_url = (
                    a["href"]
                    if a["href"].startswith("http")
                    else "https://www.shl.com" + a["href"]
                )

                row = a.find_parent("tr")

                if not row:
                    row = a.find_parent("tr")

                adaptive_support = "No"  # ddefault

                if row:
                    cells = row.find_all("td")

                    if len(cells) >= 3:
                        adaptive_cell = cells[2]
                        # green circle check
                        circle = adaptive_cell.find(
                            "span",
                            class_=lambda c: c
                            and "catalogue__circle" in c
                            and "-yes" in c,
                        )
                        if circle:
                            adaptive_support = "Yes"

                if full_url not in all_products_map:
                    all_products_map[full_url] = {
                        "url": full_url,
                        "adaptive_support": adaptive_support,
                    }
                    new_found_count += 1

            print(f"Found {new_found_count} new products on this page.")

            if new_found_count == 0:
                print(f"Stopping pagination. Total found: {len(all_products_map)}")
                break

            start += batch_size
            time.sleep(1)

    except Exception as e:
        print(f"Critical Error: {e}")

    finally:
        print("Closing driver...")
        driver.quit()

    return list(all_products_map.values())


if __name__ == "__main__":
    products = get_links_with_adaptive_info()
    print(f"Saving {len(products)} products to JSON...")

    with open("shl_links_with_adaptive.json", "w") as f:
        json.dump(products, f, indent=2)

    print("Done. File saved: shl_links_with_adaptive.json")
