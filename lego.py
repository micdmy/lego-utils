from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pickle
import random
import json

def update_results_json(set_number, available_items, unavailable_items, filename="results.json"):
    # Try to load existing data
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # Overwrite or add the set_number entry
    data[set_number] = {
        "available": available_items,
        "unavailable": unavailable_items
    }

    # Save back to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Updated results for set {set_number} in {filename}")


class PartProcessingError(Exception):
    def __init__(self,  message, piece_number = "not_given"):
        super().__init__(f"[{piece_number}] {message}")
        self.piece_number = piece_number
        self.message = message

# Set up Chrome options (optional: run headless)
chrome_options = Options()
chrome_options.binary_location = "/usr/bin/chromium"  # Browser
# chrome_options.add_argument("--headless")

# Path to your ChromeDriver executable
service = Service("/usr/bin/chromedriver")

driver = webdriver.Chrome(service=service, options=chrome_options)
# Configure to use Brave

products = ["4891", "8216", "4792", "8236", "8065"]


def go_to_product(driver, subpath):
    base_url = "https://www.lego.com/pl-pl/service/replacement-parts/broken"
    # Ensure there's exactly one slash between base and subpath
    full_url = base_url.rstrip("/") + "/" + subpath.lstrip("/").rstrip("/") + "/pieces?search=*" 
    driver.get(full_url)


def wait_and_click_random_reason(driver, timeout=10):
    """
    Waits for the broken reason modal to appear, then randomly clicks one of the first 5 reason buttons.
    """
    try:
        wait = WebDriverWait(driver, timeout)

        # Wait for the modal heading to confirm it's open
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//h2[contains(text(), 'Element jest')]")
        ))

        # Now grab all reason buttons
        reason_buttons = driver.find_elements(
            By.CSS_SELECTOR, "button[data-test^='piece-broken-reason-']"
        )
    except Exception as e:
        raise PartProcessingError(f"click_reason failed")

    if len(reason_buttons) >= 5:
        chosen = random.choice(reason_buttons[:5])
        chosen.click()
    else:
        raise PartProcessingError(f"not enough ({len(reason_buttons)}) reason buttons")



def is_part_available_by_structure(driver, timeout=10):
    """
    Checks if the part is available by verifying that the out-of-stock message
    does NOT appear between the heading and the part list.
    """
    try:
        # wAit for it and get the heading element
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-test='view-set-heading']")
            )
        )
        heading = driver.find_element(By.CSS_SELECTOR, "[data-test='view-set-heading']")

        # Get the parent container of the heading
        parent = heading.find_element(By.XPATH, "./..")

        # Get all direct children of the parent
        children = parent.find_elements(By.XPATH, "./*")

        # Find the index of the heading
        heading_index = children.index(heading)

        # Look for out-of-stock message between heading and part list
        for i in range(heading_index + 1, len(children)):
            tag = children[i].tag_name
            if tag == "p" and children[i].get_attribute("data-test") == "out-of-stock-text":
                return False  # Part is unavailable
            if tag == "ul":
                return True  # Part list follows heading directly → available

        # If neither found:
        raise PartProcessingError(f"is_part_available_by_structure not found expected html elements")

    except Exception as e:
        raise PartProcessingError(f"is_part_available_by_structure failed: {e}")


def delete_item_by_piece_number(driver, product_id, timeout=10):
    """
    Deletes an item from the basket by its product ID.
    
    :param driver: Selenium WebDriver instance
    :param product_id: The product ID string (e.g., "4639695")
    :param timeout: Max seconds to wait for the delete button
    """
    wait = WebDriverWait(driver, timeout)

    # Build a CSS selector that matches the delete button with the product ID
    selector = f"button[data-test^='delete-part-button'][data-test*='{product_id}']"

    try:
        delete_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        delete_btn.click()
        print(f"Deleted item with product ID: {product_id}")
    except Exception as e:
        raise PartProcessingError(f"delete_item_by_piece_number failed: {e}", product_id)


def confirm_deletion(driver, timeout=10):
    """
    Waits for the deletion confirmation dialog and clicks the 'Tak' button.
    """
    wait = WebDriverWait(driver, timeout)

    try:
        confirm_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test$='remove-part-button']"))
        )
        confirm_btn.click()

    except Exception as e:
        raise PartProcessingError(f"confirm_deletion failed: {e}")


def check_items(driver):
    available_items = []
    unavailable_items = []

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
        try:
            piece_number = product.find_element(
                By.CSS_SELECTOR, "[data-test='piece-number']"
            ).text.strip()
        except Exception as e:
            print(f"Error finding piece-number text {piece_number}: {e}")
            continue
        try:
            # Click 'Wybierz'
            select_btn = product.find_element(
                By.CSS_SELECTOR, "[data-test='piece-select-link']"
            )
        except Exception as e:
            print(f"Error finding select product button {piece_number}: {e}")
            continue

        try:
            select_btn.click()
        except Exception as e:
            print(f"Error with piece {piece_number}: {e}")
            continue
        try:
            wait_and_click_random_reason(driver)
        except Exception as e:
            print(f"Error with piece {piece_number}: {e}")
            continue
        try:
            if is_part_available_by_structure(driver):
                print("AVAILABLE")
                available_items.append(piece_number)
            else:
                unavailable_items.append(piece_number)
                print("NOT AVAILABLE")
                delete_item_by_piece_number(driver, piece_number)
                confirm_deletion(driver)
                wait = WebDriverWait(driver, 10)

            driver.back()

        except Exception as e:
            print(f"Error with piece {piece_number}: {e}")
            continue

    return available_items, unavailable_items


try:
    driver.get("https://www.lego.com/pl-pl/service/replacement-parts/broken")
    cookies = pickle.load(open("lego-cookies-pop-up.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)

# Refresh with cookies applied
    driver.refresh()


    driver.get("https://www.lego.com/pl-pl/service/replacement-parts/broken")

    for set_number in  products:
        go_to_product(driver, set_number)
        (available, unavailable) = check_items(driver)
        print(f"set {set_number} availeble:")
        for a in available:
            print(a)
        print("unavailable:")
        for u in unavailable:
            print(u)
        update_results_json(set_number, available_items=available, unavailable_items=unavailable)


    
finally:
    driver.quit()



