import asyncio
from playwright.async_api import async_playwright

async def get_page_source():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://radaris.com/ng/search?ff=Rayko&fl=Bellmas"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)
            content = await page.content()
            with open("radaris_search_copy.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully saved page source to radaris_search_copy.html")
            
            # Also take a screenshot to be sure
            await page.screenshot(path="radaris_search_screenshot.png")
            print("Successfully saved screenshot to radaris_search_screenshot.png")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_page_source())
