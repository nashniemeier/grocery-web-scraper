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

		await page.goto(url, wait_until="domcontentloaded")
		print("Page Title:", await page.title())


		# Changing Location
		await page.locator('button[class="store-flyout-button d-flex "]').click()
		location_search = page.locator('input[placeholder="Search by Zip or City, State"]')
		await location_search.fill(str(zipcode))
		await location_search.press("Enter")

		await page.locator('div[data-testid="ads-radio-button__selectable-card"]').first.click()
		#await page.wait_for_timeout(2000)
		await page.get_by_role("button", name="Continue shopping").click()

		# Now to get product cards
		card_locator = page.locator('article[class="product-tile"]')


		await card_locator.nth(4).wait_for(state='visible', timeout=15000)

		cards = await card_locator.all()
		print(f'Found {len(cards)} products using class.')

		print('\n')

		# First line = title
		# Third line = price
		# If price has '/', then get the next few lines

		for card in cards[:5]:
			full_text = await card.inner_text()

			lines = [line.strip() for line in full_text.split('\n') if line.strip()]

			print(lines)
			title = None
			volume = None
			price = None
			for line in lines:
				if title == None and item_name.lower() in line.lower():
					title = line
				if price == None and '$' in line:
					price = line

			print("PRICE = ", price)
			print("TITLE = ", title)


			print('\n\n')

		await browser.close()

print("----------------- Chicken ----------------\n")
asyncio.run(scrape("beef", 47906))
print("-~-~-~-~-~-~-~-~-~ MILK ~-~-~-~-~-~-~-~-~-\n")
asyncio.run(scrape("bread", 47906))
print("------------------ EGGS ------------------\n")
asyncio.run(scrape("hot dog", 47906))
