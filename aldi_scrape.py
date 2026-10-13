import asyncio
from playwright.async_api import async_playwright, Playwright
from urllib.parse import quote

grocery_list = ["milk", "eggs", "chicken*", "beef broth"]
is_meat = []


# This function takes raw cards of text from the HTML of the website and cleans
# the text into usable data. Accepts the raw cards and a list to store the data
async def parse_cards(cards, parsed_products, item_name):

	if '*' in item_name:
		item_name = item_name.replace('*', '')
	print('*' * 10, item_name, '*' * 10)

	for card in cards[:5]:

		# Grab all text
		full_text = await card.inner_text()
		
		# Split into individual lines
		lines = [line.strip() for line in full_text.split('\n') if line.strip()]

		title = None
		price = None
		volume = None
		price_per_unit = None
		unit = None

		# For meat/per volume items only
		meat_produce_volume = None

		for index, line in enumerate(lines):
			# Get the price value
			if '$' in line and price == None:
				price = line[line.index('$'):(line.index('.') + 3)]
			# Specifically for meat
			if '$' in line and '/' in line:
				price_per_unit = line
			elif item_name.lower().strip() in line.lower() and title == None:
				title = line
				volume = lines[index + 1]
				meat_produce_volume = lines[index + 2]

		if volume:
			if 'about' in volume.lower():
				volume_details = volume.split(' ')

				if price_per_unit == None:
					price_per_unit = volume_details[0]
				
				volume = volume[volume.index('t'):(volume.index('.') + 2)].strip()
			elif '$' in volume and '/' in volume:
				price_per_unit = volume
			else:
				price_per_unit = price + ' / ' + volume

		if price_per_unit:
			ppunit_num = float(price_per_unit.split()[0][1:])

		details = {
			"STORE": "Aldi",
			"PRICE": price,
			"TITLE": title,
			"VOLUME": volume,
			"PPUNIT": price_per_unit,
			"PRICE_NUM": float(price[1:]),
			"PPUNIT_NUM": ppunit_num
		}
		parsed_products.append(details)

# Finds the cheapest option. Accepts a list of parsed items, prints and returns
# the cheapest item (type: dictionary)
def cheapest_option(items, is_meat_val):
	
	if is_meat_val:
		cheapest = min(items, key=lambda item: item["PPUNIT_NUM"])
	else:
		cheapest = min(items, key=lambda item: item["PRICE_NUM"])
	
	print("The cheapest item is:\n")
	print_item([cheapest])
	return [cheapest]


# Accepts a list of parsed items and prints them.
def print_item(items):
	for details in items:
		print("PRICE: ", details["PRICE"])
		print("TITLE: ", details["TITLE"])
		print("VOLUME: ", details["VOLUME"])
		print("PPUNIT: ", details["PPUNIT"])
		print("PPUNIT_NUM: ", details["PPUNIT_NUM"])
		print('\n\n')


async def browser_setup(grocery_list, zipcode):
	async with async_playwright() as playwright:
		# Fix item name to prevent suggested, non searched items
		items = [item + " " for item in grocery_list]

		for item in items:
			if '*' in item:
				item.replace('*', '')
				is_meat.append(True)
			else:
				is_meat.append(False)

		# Start up playwright for our page
		start_url = "https://www.aldi.us/store/aldi/s?k="
		browser = await playwright.chromium.launch(
				headless=False,
				channel='chromium'
		)
		page = await browser.new_page()

		# Build our search url
		url = start_url + quote(items[0])
		print(url)

		# Go to the page
		await page.goto(url, wait_until="domcontentloaded")

		# Next click pickup
		pickup_btn = page.get_by_role("button", name="In-Store")
		await pickup_btn.wait_for(state='visible', timeout=10000)
		await pickup_btn.click()

		# Change Store Click
		await page.get_by_role('button', name='Change store').nth(1).click()

		# Entering the zipcode
		await page.locator('.e-1wlht9u').click()
		await page.locator('.e-t267xt').fill(str(zipcode))
		await page.locator('.e-616lx5').click()

		# Selecting the store, picking the first one that shows up
		await page.locator('.e-5irn7x').first.click()
		await page.wait_for_load_state("domcontentloaded")
		await page.get_by_role('button', name='Shop this store').click()
		await page.wait_for_load_state("domcontentloaded")
		await page.wait_for_timeout(10000)

		# Browser is set up, lets scrape
		await scrape(items, page, start_url)

async def scrape(items, page, start_url):
	async with async_playwright() as playwright:

		for index, item_name in enumerate(items):
			# Getting item cards
			card_locator = page.locator('a[data-item-card-button="true"]')
			await card_locator.nth(4).wait_for(state='visible', timeout=15000)

			#await page.wait_for_timeout(2000)
			cards = await card_locator.all()

			# End of playwright commands
			parsed_products = []
			await parse_cards(cards, parsed_products, item_name)

			if index + 1 < len(items):
				url = start_url + quote(items[index + 1])
				await page.goto(url, wait_until="domcontentloaded")

			cheapest_option(parsed_products, is_meat[index])


asyncio.run(browser_setup(grocery_list, 47906))
