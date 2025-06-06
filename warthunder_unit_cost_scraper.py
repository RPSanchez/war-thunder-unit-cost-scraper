import requests
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Constants for HTTP headers to mimic a real browser request
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/114.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://wiki.warthunder.com",
    "Connection": "keep-alive"
}

# Base URL of War Thunder Wiki
BASE_URL = "https://wiki.warthunder.com"

# Time delay between requests (seconds) to reduce risk of server blocking
REQUEST_DELAY = 1.5

# Number of retry attempts per request
MAX_RETRIES = 5

# Number of parallel threads for fetching unit data
CONCURRENT_WORKERS = 3

# Thread lock to ensure thread-safe printing
print_lock = threading.Lock()

def fetch_with_retries(session, url):
    """
    Fetch a URL with retry and exponential backoff on failure or rate limiting.

    Args:
        session (requests.Session): The HTTP session to use.
        url (str): The URL to fetch.

    Returns:
        str or None: HTML content if successful; None otherwise.
    """
    backoff = 1
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                return response.text
            elif response.status_code in (403, 405, 429):
                with print_lock:
                    print(f"[WARN] {response.status_code} on {url}, backing off {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
            else:
                with print_lock:
                    print(f"[ERROR] Unexpected status {response.status_code} on {url}")
                break
        except requests.RequestException as e:
            with print_lock:
                print(f"[ERROR] Exception {e} on {url}, retry {attempt + 1}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
    return None

def get_unit_urls(session, tech_tree_path):
    """
    Extract all unit URLs from a given tech tree page.

    Args:
        session (requests.Session): The HTTP session to use.
        tech_tree_path (str): Tech tree path relative to the base URL.

    Returns:
        list[str]: List of unit relative URLs.
    """
    url = f"{BASE_URL}/{tech_tree_path}?v=t"
    print(f"[STEP] Fetching unit URLs from {url}")
    html = fetch_with_retries(session, url)
    if not html:
        print(f"[ERROR] Failed to fetch tech tree page {url}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    unit_divs = soup.select("div.wt-tree_item")
    print(f"[INFO] Found {len(unit_divs)} units in {tech_tree_path}")
    urls = []
    for div in unit_divs:
        link = div.find("a", class_="wt-tree_item-link")
        if link and link.get("href"):
            urls.append(link.get("href"))
    return urls

def extract_total_cost(session, unit_url, index, total_units):
    """
    Extract the total GE cost (Talisman + Aces) for a single unit page.

    Args:
        session (requests.Session): The HTTP session to use.
        unit_url (str): The relative URL of the unit page.
        index (int): Current processing unit index (for progress output).
        total_units (int): Total number of units to process.

    Returns:
        int: Total GE cost for the unit. 0 if none found or on failure.
    """
    # Delay to avoid overwhelming the server
    time.sleep(REQUEST_DELAY)

    full_url = BASE_URL + unit_url
    html = fetch_with_retries(session, full_url)
    if not html:
        with print_lock:
            print(f"[ERROR] Failed to fetch unit page {full_url}")
        return 0

    soup = BeautifulSoup(html, "html.parser")

    talisman_cost = 0
    aces_cost = 0

    # Extract Talisman cost if present
    talisman_divs = soup.find_all("div", class_="game-unit_chars-line")
    for div in talisman_divs:
        header = div.find("span", class_="game-unit_chars-header")
        if header and header.text.strip() == "Talisman cost":
            val_span = div.find("span", class_="game-unit_chars-value")
            if val_span:
                text = val_span.get_text(strip=True).replace(",", "")
                try:
                    talisman_cost = int(''.join(filter(str.isdigit, text)))
                except Exception:
                    talisman_cost = 0
            break

    # Extract Aces cost if present
    aces_divs = soup.find_all("div", class_="game-unit_chars-subline")
    for div in aces_divs:
        span = div.find("span")
        if span and span.text.strip() == "Aces":
            val_span = div.find("span", class_="game-unit_chars-value")
            if val_span:
                text = val_span.get_text(strip=True).replace(",", "")
                try:
                    aces_cost = int(''.join(filter(str.isdigit, text)))
                except Exception:
                    aces_cost = 0
            break

    total = talisman_cost + aces_cost
    with print_lock:
        print(f"[INFO] Processing unit {index}/{total_units} - {unit_url}: "
              f"Talisman={talisman_cost}, Aces={aces_cost}, Total={total}")
    return total

def main():
    """
    Main function to coordinate scraping all tech trees and calculating total GE cost.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    print("[STEP] Initializing session with homepage fetch")
    home_resp = session.get(BASE_URL, timeout=10)
    if home_resp.status_code != 200:
        print(f"[WARN] Homepage returned {home_resp.status_code}, continuing anyway")

    # Tech tree categories to parse
    tech_trees = [
        "aviation",
        "helicopters",
        "ground",
        "ships",
        "boats"
    ]

    all_unit_urls = []
    for tree in tech_trees:
        unit_urls = get_unit_urls(session, tree)
        all_unit_urls.extend(unit_urls)

    total_units = len(all_unit_urls)
    print(f"[STEP] Total units found: {total_units}")

    total_cost = 0

    # Use ThreadPoolExecutor with limited concurrency to avoid rate limiting
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = {
            executor.submit(extract_total_cost, session, url, idx + 1, total_units): url
            for idx, url in enumerate(all_unit_urls)
        }

        for future in as_completed(futures):
            total_cost += future.result()

    print(f"[RESULT] Total GE cost of all units: {total_cost}")

if __name__ == "__main__":
    main()
