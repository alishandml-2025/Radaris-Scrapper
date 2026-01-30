import json
import csv
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# CONFIGURATION
INPUT_FILE = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber\radaris_search_queue.csv')
OUTPUT_FILE = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber\radaris_test_results.json')
SAMPLE_SIZE = 3 

def test_scraper():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    print("--- Radaris Scraper Test Mode (Standard Selenium) ---")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        queue = list(reader)[:SAMPLE_SIZE]

    print("Initializing browser...")
    chrome_options = Options()
    # Masking automation
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("window-size=1280,800")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    # Use webdriver-manager to handle driver versions automatically
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute CDP command to hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    results = []
    try:
        for i, row in enumerate(queue):
            name = row['Owner Name']
            url = row['Radaris Search URL']
            
            print(f"\n[{i+1}/{SAMPLE_SIZE}] Searching for: {name}")
            print(f"URL: {url}")
            driver.get(url)
            
            # Wait for content
            time.sleep(random.uniform(7, 10))
            
            # Diagnostic: Print page title
            print(f"Page Title: {driver.title}")
            
            try:
                # Radaris search results usually have profiles in a specific container
                # We'll try to find all profile links and filter them by the search name
                wait = WebDriverWait(driver, 15)
                
                # Broad selector for any link containing '/p/' which is a profile link
                profile_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"]')
                
                print(f"Total potential profile links found: {len(profile_elements)}")
                
                # Categorize and filter profiles
                best_match = None
                
                # Normalize search name for comparison
                search_parts = set(name.lower().split())

                for el in profile_elements:
                    text = el.text.strip()
                    href = el.get_attribute('href')
                    if not text or not href:
                        continue
                        
                    # Basic name matching: check if many parts of the name match
                    text_lower = text.lower()
                    match_count = sum(1 for part in search_parts if part in text_lower)
                    
                    # Log some candidates for debugging
                    if match_count > 0:
                        print(f" - Candidate match: {text} | Score: {match_count}")
                        if best_match is None or match_count > best_match['score']:
                            best_match = {
                                "name": text,
                                "url": href,
                                "score": match_count
                            }
                
                if best_match:
                    profile_url = best_match['url']
                    print(f"SUCCESS: Best profile found - {best_match['name']} ({profile_url})")
                    
                    # --- DEEP EXTRACTION START ---
                    print(f"Navigating to profile for deep extraction...")
                    driver.get(profile_url)
                    time.sleep(random.uniform(5, 8))
                    
                    phones = []
                    try:
                        # Try to find elements that look like phone numbers or sections
                        # Radaris often has phone sections or 'View' buttons
                        # We'll look for text patterns that match phone numbers
                        import re
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_text)
                        phones = list(set(phone_matches)) # Deduplicate
                        
                        if phones:
                            print(f"Found {len(phones)} potential phone numbers: {', '.join(phones)}")
                        else:
                            print("No visible phone numbers found on profile page.")
                    except Exception as extraction_err:
                        print(f"Extraction error: {extraction_err}")
                    
                    results.append({
                        **row,
                        "radaris_display_name": best_match['name'],
                        "radaris_profile_url": profile_url,
                        "phones": phones,
                        "match_score": best_match['score']
                    })
                    # --- DEEP EXTRACTION END ---
                else:
                    print(f"No strong matches found for {name} among results.")
                    
            except Exception as e:
                print(f"Search failed: {str(e)[:100]}")
            
            if i < SAMPLE_SIZE - 1:
                delay = random.uniform(5, 12)
                print(f"Waiting {delay:.1f}s...")
                time.sleep(delay)

    finally:
        driver.quit()

    # Save results to a test file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Also save to CSV for easy access
    csv_output = OUTPUT_FILE.with_suffix('.csv')
    if results:
        headers = list(results[0].keys())
        # Flatten phones list for CSV
        for r in results:
            if 'phones' in r:
                r['phones'] = ", ".join(r['phones'])
        
        with open(csv_output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\nExtracted data saved to:\n - {OUTPUT_FILE}\n - {csv_output}")

if __name__ == "__main__":
    test_scraper()
