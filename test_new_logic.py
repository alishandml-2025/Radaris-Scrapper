import asyncio
import json
import re
from playwright.async_api import async_playwright
import random

TIMEOUT = 90000

async def scrape_radaris_profile(context, row):
    name = row['Owner Name']
    url = row['Radaris Search URL']
    
    page = await context.new_page()
    try:
        print(f"Searching for: {name}...")
        await page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
        await asyncio.sleep(5)
        
        # --- IMPROVED PROFILE LINK DETECTION ---
        best_match = None
        search_parts = set(name.lower().split())

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
                        if p_name and p_url:
                            score = sum(1 for part in search_parts if part in p_name)
                            if score > 0:
                                if best_match is None or score > best_match['score']:
                                    best_match = {"name": item["name"], "url": p_url, "score": score}
            except:
                continue

        if not best_match:
            elements = await page.query_selector_all('[data-href*="/~"]')
            for el in elements:
                try:
                    href = await el.get_attribute('data-href')
                    text = (await el.inner_text()).strip()
                    if href and text:
                        score = sum(1 for part in search_parts if part in text.lower())
                        if score > 0:
                            if best_match is None or score > best_match['score']:
                                best_match = {"name": text, "url": href, "score": score}
                except:
                    continue

        if not best_match:
            print(f"No match found for {name}")
            return {"status": "no_match"}

        profile_url = best_match['url']
        if not profile_url.startswith('http'):
            profile_url = f"https://radaris.com{profile_url}" if profile_url.startswith('/') else f"https://radaris.com/{profile_url}"
            
        print(f"Found best match: {best_match['name']} (Score: {best_match['score']})")
        print(f"Navigating to: {profile_url}")

        await page.goto(profile_url, wait_until="networkidle", timeout=TIMEOUT)
        await asyncio.sleep(5)
        
        # --- ROBUST PHONE EXTRACTION FROM JSON-LD ---
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

        phones = list(set([p.strip() for p in phones if p]))

        if not phones:
            page_content = await page.content()
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phones = list(set(re.findall(phone_pattern, page_content)))
        
        print(f"Extracted {len(phones)} phones for {name}")
        return {
            "name": name,
            "display_name": best_match['name'],
            "url": profile_url,
            "phones": phones,
            "status": "success"
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        row = {
            "Owner Name": "RAYKO BELLMAS",
            "Radaris Search URL": "https://radaris.com/ng/search?ff=RAYKO&fl=BELLMAS&where=HIALEAH%2C+FL"
        }
        result = await scrape_radaris_profile(context, row)
        print(json.dumps(result, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
