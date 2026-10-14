import asyncio
from playwright.async_api import async_playwright
from urllib.parse import quote

grocery_list = ["eggs", "chicken", "milk", "onion"]



async def browser_setup(items, zipcode):
	async with async_playwright() as p:
		# Launch using Playwright's built-in Chromium
		browser = await p.chromium.launch(
			headless=False,
			channel="chromium",
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
		url = base_url + quote(items[0])

		await page.goto(url, wait_until="domcontentloaded")

		# Changing Location
		await page.locator('button[class="store-flyout-button d-flex "]').click()
		location_search = page.locator('input[placeholder="Search by Zip or City, State"]')
		await location_search.fill(str(zipcode))
		await location_search.press("Enter")

		await page.locator('div[data-testid="ads-radio-button__selectable-card"]').first.click()
		#await page.wait_for_timeout(2000)
		await page.get_by_role("button", name="Continue shopping").click()

		await scrape(page, items, base_url)


# Gets the product cards from the website
async def scrape(page, items, start_url):

	for index, item in enumerate(items):

		# Now to get product cards
		card_locator = page.locator('article[class="product-tile"]')

		await card_locator.nth(4).wait_for(state='visible', timeout=15000)

		cards = await card_locator.all()
		
		# Create a list and parse items into that list
		parsed_products = []
		await parse_cards(cards, parsed_products, item)

		if index + 1 < len(items):
			url = start_url + quote(items[index + 1])
			await page.goto(url, wait_until="domcontentloaded")


async def parse_cards(cards, parsed_products, item_name):

	is_meat = False
	if '*' in item_name:
		item_name = item_name.replace('*', '')
		is_meat = True
	print('*' * 10, item_name, '*' * 10)

	for card in cards[:5]:
		full_text = await card.inner_text()

		# Split all lines into an array
		lines = [line.strip() for line in full_text.split('\n') if line.strip()]

		# Establish needed variables
		title = None
		price = None
		deal = None
		volume = None
		price_per_unit = None
		unit = None

		# Parse line by line
		for line, next_line in zip(lines, lines[1:]):
			if title == None and item_name.lower() in line.lower():
				title = line
			elif price == None and '$' in line:
				price = line
			elif 'reviews' in line and next_line != "Subscribe":
				deal = next_line
			elif 'Approx' in line and volume == None:
				volume_details = line.split(' ')
				unit = volume_details[2]
				price_per_unit = volume_details[0] + ' / ' + unit
				volume = volume_details[5] + unit

		# For difficult titles
		if title == None:
			if lines[0] == "Sponsored":
				title = lines[1]
			else:
				title = lines[0]

		# Parsing volume from title where approx volume is not given
		if ',' in title and volume == None:
			volume = title[(title.rindex(',') + 1):].strip()
			price_per_unit = price + ' / ' + volume
		elif volume != None and ' ' in volume:
			price_per_unit = '$' + str(
					round(int(volume[:volume.index(' ')])
					/ float(price[1:]), 2)
			)
			unit = volume[(volume.index(' ') + 1):]

		price_num = float(price[1:(price.index('.') + 3)])

		details = {
			"STORE": "Meijer",
			"PRICE": price,
			"TITLE": title,
			"VOLUME": volume,
			"PPUNIT": price_per_unit,
			"PRICE_NUM": price_num
		}

		print("TITLE:", details["TITLE"])
		print("PRICE:", details["PRICE"])
		print("PRICE_NUM:", details["PRICE_NUM"])

		print('\n\n')

asyncio.run(browser_setup(grocery_list, 47906))
