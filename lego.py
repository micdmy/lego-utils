import argparse
import json
import pickle

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

COOKIES_FILE = "lego-cookies-pop-up.pkl"
INITIAL_URL = "https://www.lego.com/pl-pl/service/replacement-parts/broken"
RESULTS_FILE = "./json_cache/available_in_shop.json"
SETS_FILE = "./lost_sets.json"


def update_results_json(set_number, elements, filename=RESULTS_FILE):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data[set_number] = {"elements": elements}

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Updated results for set {set_number} in {filename}")


def create_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium"
    # chrome_options.add_argument("--headless")
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)


def load_cookies_from_file(driver, cookies_file=COOKIES_FILE):
    with open(cookies_file, "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)
    print(f"Loaded cookies from {cookies_file}")


def save_cookies_to_file(driver, cookies_file=COOKIES_FILE):
    cookies = driver.get_cookies()
    with open(cookies_file, "wb") as f:
        pickle.dump(cookies, f)
    print(f"Saved cookies to {cookies_file}")


def handle_cookies(driver, save_cookies):
    driver.get(INITIAL_URL)

    if save_cookies:
        print("Now click cookies banner and press enter")
        input()
        save_cookies_to_file(driver)
    else:
        try:
            load_cookies_from_file(driver)
            driver.refresh()
        except FileNotFoundError:
            print(f"Cookie file '{COOKIES_FILE}' not found. Run with --save-cookies first.")


def go_to_product(driver, subpath):
    full_url = (
        INITIAL_URL.rstrip("/")
        + "/"
        + subpath.lstrip("/").rstrip("/")
        + "/pieces?search=*"
    )
    driver.get(full_url)


def show_all_pieces_if_needed(driver, timeout=5):
    wait = WebDriverWait(driver, timeout)
    try:
        button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-test='show-all-pieces-button']")
        ))
        button.click()
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-test='piece-number']")
        ))
    except Exception:
        pass


def find_piece_items(driver):
    items = driver.find_elements(By.CSS_SELECTOR, "[data-test='piece-search-result']")
    if not items:
        items = driver.find_elements(By.CSS_SELECTOR, "li[class*='GridItem']")
    return items

def collect_set_elements(driver):
    available_items = []

    wait = WebDriverWait(driver, 10)

    # Find all products
    products = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "li.GridItem_gridItem__3hyna")
    ))
    number_of_products = len(products)
    for i in range(number_of_products):
        if i > 0 :
            wait = WebDriverWait(driver, 10)
            # reload products
            products = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.GridItem_gridItem__3hyna")))
        product = products[i]
        piece = {}
        try:
            piece_number = product.find_element(
                By.CSS_SELECTOR, "[data-test='piece-number']"
            ).text.strip()
            #print(f"piece number {piece_number}")
            piece["lego_id"] = str(piece_number)
        except Exception as e:
            print(f"Error finding piece-number text {piece_number}: {e}")
            continue
        try:
            piece_description = product.find_element(
                By.CSS_SELECTOR, "[data-test='piece-title']"
            ).text.strip()
            print(f"piece desc {piece_description}")
            piece["description"] = str(piece_description)
        except Exception as e:
            print(f"Error finding piece-description text {piece_description}: {e}")
        available_items.append(piece)
            
    return available_items

def main():
    parser = argparse.ArgumentParser(description="Scrape available LEGO replacement parts for sets")
    parser.add_argument(
        "--save-cookies",
        action="store_true",
        help="Wait for manual cookie banner acceptance, then save cookies to file",
    )
    parser.add_argument('-p', '--load_products', action="store_true",
                        help = 'load products form json_cache/lost_sets.json')

    args = parser.parse_args()

    all_sets = {}

    if args.load_products:
        with open("./json_cache/lost_sets.json", 'r') as f:
            products = json.load(f)
            products = [(p[0]) for p in products if p[0] != "fig"]
    else:
        products = ["6115"]


    driver = create_driver()
    try:
        handle_cookies(driver, args.save_cookies)
        failed_sets = []
        for set_number in products:
            go_to_product(driver, set_number)
            try:
                elements = collect_set_elements(driver)
            except Exception as e:
                print(f"PROBLEM with set {set_number}: {e}")
                failed_sets.append(set_number)
                continue
            all_sets[set_number] = elements
            update_results_json(set_number, elements)

            print(f"set {set_number} ({len(elements)} elements):")
            #for element in elements:
            #    print(f"  {element}")
    finally:
        driver.quit()

    return all_sets


if __name__ == "__main__":
    main()
