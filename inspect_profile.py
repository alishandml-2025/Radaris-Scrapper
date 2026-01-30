import asyncio
from playwright.async_api import async_playwright

async def get_profile_source():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        # The URL provided by the user
        url = "https://radaris.com/~Rayko-Bellmas/1700417647"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)
            content = await page.content()
            with open("radaris_profile_copy.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully saved profile source to radaris_profile_copy.html")
            
            # Also take a screenshot to be sure
            await page.screenshot(path="radaris_profile_screenshot.png")
            print("Successfully saved screenshot to radaris_profile_screenshot.png")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_profile_source())
