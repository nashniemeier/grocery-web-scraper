import asyncio
from playwright.async_api import async_playwright
from urllib.parse import quote
async def scrape(item_name, zipcode):
	async with async_playwright() as p:
		# Launch using Playwright's built-in Chromium
		browser = await p.chromium.launch(
			headless=False,
			args=[
				"--disable-blink-features=AutomationControlled", # Prevents navigator.webdriver detection
				"--start-maximized"
			]
		)

		context = await browser.new_context(
			user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
			viewport={"width": 1920, "height": 1080},
			locale="en-US"
		)

		page = await context.new_page()

		# Mask navigator.webdriver flag
		await page.add_init_script("""
			Object.defineProperty(navigator, 'webdriver', {
				get: () => undefined
			});
		""")


		# Setting the URL

		base_url = 'https://www.meijer.com/shopping/search.html?text='
		url = base_url + quote(item_name)

		await page.goto("https://www.meijer.com", wait_until="domcontentloaded")
		print("Page Title:", await page.title())


		# Changing Location
		await page.locator('button[class="store-flyout-button d-flex "]').click()
		location_search = page.locator('input[placeholder="Search by Zip or City, State"]')
		await location_search.fill(str(zipcode))
		await location_search.press("Enter")

		await page.locator('div[data-testid="ads-radio-button__selectable-card"]').first.click()
		await page.wait_for_timeout(2000)
		await page.get_by_role("button", name="Continue shopping").click()

		await page.wait_for_timeout(200000)
		await browser.close()

asyncio.run(scrape("chicken", 47906))
