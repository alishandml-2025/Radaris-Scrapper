import asyncio
import csv
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright
import random

# CONFIGURATION
INPUT_FILE = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber\radaris_search_queue.csv')
OUTPUT_FILE = Path(r'c:\Users\mento\OneDrive\Desktop\phoneNumber\radaris_test_results.json')
MAX_CONCURRENT_PAGES = 1  # Keep it low to avoid detection
BATCH_SIZE = 5           # Set to 5 for "5/5 names per run" as requested
TIMEOUT = 90000           # Increased timeout to 90s for slow loads

async def scrape_radaris_profile(context, row):
    """
    Scrapes a Radaris search results page, identifies the best profile match,
    and extracts phone numbers from the profile page.
    """
    name = row['Owner Name']
    url = row['Radaris Search URL']
    
    page = await context.new_page()
    try:
        print(f"Searching for: {name} in {row.get('City', '')}, {row.get('State', '')}...")
        await page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
        
        # Give it a moment to render
        await asyncio.sleep(random.uniform(5, 8))
        
        # Check for 'No results' or 'Bot detection'
        content = await page.content()
        if "Access Denied" in content or "Checking your browser" in content:
            print(f"WARNING: Bot detection or access denied for {name}.")
            return {**row, "status": "blocked"}

        # --- IMPROVED PROFILE LINK DETECTION WITH LOCATION MATCHING ---
        best_match = None
        search_parts = set(name.lower().split())
        target_city = row.get('City', '').lower().strip()
        target_state = row.get('State', '').lower().strip()

        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for script in scripts:
            try:
                json_text = await script.inner_text()
                data = json.loads(json_text)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "Person":
                        p_name = item.get("name", "").lower()
                        p_url = item.get("@id") or item.get("url")
                        
                        # Extract location info for scoring
                        p_city = ""
                        p_state = ""
                        home_loc = item.get("homeLocation")
                        if home_loc and isinstance(home_loc, dict):
                            addr = home_loc.get("address")
                            if addr and isinstance(addr, dict):
                                p_city = addr.get("addressLocality", "").lower()
                                p_state = addr.get("addressRegion", "").lower()

                        if p_name and p_url:
                            # 1. Name matching score
                            name_score = sum(1 for part in search_parts if part in p_name)
                            
                            # 2. Location matching score (Bonus for precision)
                            loc_score = 0
                            if target_city and target_city in p_city:
                                loc_score += 2
                            if target_state and (target_state in p_state or target_state == p_state.strip('.')):
                                loc_score += 1
                                
                            total_score = name_score + loc_score
                            
                            if name_score > 0:
                                if best_match is None or total_score > best_match['score']:
                                    best_match = {
                                        "name": item["name"], 
                                        "url": p_url, 
                                        "score": total_score,
                                        "city": p_city,
                                        "state": p_state
                                    }
            except:
                continue

        # 2. Fallback to UI elements if no JSON-LD match
        if not best_match:
            # Look for cards/elements that might have data-href and location text
            # Radaris often has location info inside the same card/container
            containers = await page.query_selector_all('.radaris-card, .search-result, [data-href*="/~"]')
            for container in containers:
                try:
                    href = await container.get_attribute('data-href') or await (await container.query_selector('a')).get_attribute('href')
                    text = (await container.inner_text()).strip().lower()
                    
                    if href and text:
                        name_score = sum(1 for part in search_parts if part in text)
                        loc_score = 0
                        if target_city and target_city in text: loc_score += 2
                        if target_state and target_state in text: loc_score += 1
                        
                        total_score = name_score + loc_score
                        
                        if name_score > 0:
                            if best_match is None or total_score > best_match['score']:
                                best_match = {"name": text.split('\n')[0], "url": href, "score": total_score}
                except:
                    continue

        if not best_match:
            print(f"No match found for {name}")
            return {**row, "status": "no_match"}

        profile_url = best_match['url']
        if not profile_url.startswith('http'):
            profile_url = f"https://radaris.com{profile_url}" if profile_url.startswith('/') else f"https://radaris.com/{profile_url}"
            
        print(f"Found best match: {best_match['name']} (Score: {best_match['score']})")
        print(f"Navigating to: {profile_url}")

        # Navigate to individual profile for deep extraction
        await page.goto(profile_url, wait_until="networkidle", timeout=TIMEOUT)
        await asyncio.sleep(random.uniform(5, 8))
        
        # --- ROBUST PHONE EXTRACTION ---
        phones = []
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for script in scripts:
            try:
                json_text = await script.inner_text()
                data = json.loads(json_text)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "Person" and "telephone" in item:
                        tel_data = item["telephone"]
                        if isinstance(tel_data, list):
                            phones.extend(tel_data)
                        else:
                            phones.append(tel_data)
            except:
                continue

        # De-duplicate
        phones = list(set([p.strip() for p in phones if p]))

        # Regex fallback: ONLY search in specific person-related divs to avoid ad noise
        if not phones:
            # Target sections likely to contain the subject's phones
            # Radaris often uses specific IDs or classes for the main person details
            subject_details = await page.query_selector('.profile-info, #phone-numbers, .phone-list')
            if subject_details:
                section_text = await subject_details.inner_text()
                phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                phones = list(set(re.findall(phone_pattern, section_text)))
        
        print(f"Extracted {len(phones)} phones for {name}")

        return {
            **row,
            "radaris_display_name": best_match['name'],
            "radaris_profile_url": profile_url,
            "phones": phones,
            "match_score": best_match['score'],
            "status": "success"
        }

    except Exception as e:
        print(f"Error scraping {name}: {e}")
        return {**row, "status": "error", "error": str(e)}
    finally:
        await page.close()

async def main():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    # Load search queue
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        queue = list(reader)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        # RESUME LOGIC: Load existing results
        results = []
        processed_urls = set()
        if OUTPUT_FILE.exists():
            try:
                with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    processed_urls = {r['Radaris Search URL'] for r in results if 'Radaris Search URL' in r}
                print(f"Loaded {len(results)} existing records from {OUTPUT_FILE.name}")
            except:
                pass

        # Filter queue for next batch
        unprocessed_queue = [row for row in queue if row['Radaris Search URL'] not in processed_urls]
        current_batch = unprocessed_queue[:BATCH_SIZE] if BATCH_SIZE else unprocessed_queue

        if not current_batch:
            print("No more records to process in the queue.")
            await browser.close()
            return

        print(f"Processing next batch of {len(current_batch)} records (Remaining in queue: {len(unprocessed_queue)})")

        for i, row in enumerate(current_batch):
            print(f"[{i+1}/{len(current_batch)}] ", end="")
            result = await scrape_radaris_profile(context, row)
            if result:
                results.append(result)
                
                # Selective save to keep progress
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
            
            await asyncio.sleep(random.uniform(4, 9))

        # Final CSV Save
        csv_output = OUTPUT_FILE.with_suffix('.csv')
        if results:
            all_keys = set()
            for r in results:
                all_keys.update(r.keys())
            headers = sorted(list(all_keys))

            csv_results = [dict(r) for r in results]
            for r in csv_results:
                if 'phones' in r and isinstance(r['phones'], list):
                    r['phones'] = ", ".join(r['phones'])
            with open(csv_output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(csv_results)

        print(f"\nDone. Saved total {len(results)} records to {OUTPUT_FILE} and {csv_output}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
