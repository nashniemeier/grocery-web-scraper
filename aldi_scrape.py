import asyncio
from playwright.async_api import async_playwright, Playwright
from urllib.parse import quote

testing = True

async def scrape(item_name, zipcode):
	async with async_playwright() as playwright:
		# Fix item name to prevent suggested, non searched items
		item_name += ' '

		# Start up playwright for our page
		start_url = "https://www.aldi.us/store/aldi/s?k="
		browser = await playwright.chromium.launch(
				headless=False,
				channel='chromium'
		)
		page = await browser.new_page()

		# Build our search url
		url = start_url + quote(item_name)
		print(url)

		# Go to the page
		await page.goto(url, wait_until="domcontentloaded")

		# Next click pickup
		pickup_btn = page.locator('.e-1pmzhru:visible', has_text='In-Store').first
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

		# Getting item cards
		card_locator = page.locator('a[data-item-card-button="true"]')
		await card_locator.nth(4).wait_for(state='visible', timeout=15000)

		#await page.wait_for_timeout(2000)
		cards = await card_locator.all()

		# End of playwright commands
		print(f'Found {len(cards)} products.')
		parsed_products = []

		# Extract information
		for card in cards[:5]:

			# Grab all text
			full_text = await card.inner_text()
			
			# Split into individual lines
			lines = [line.strip() for line in full_text.split('\n') if line.strip()]

			print(lines)

			title = None
			price = None
			volume = None
			price_per_unit = None
			unit = None

			# For meat/per volume items only
			meat_produce_volume = None

			for index, line in enumerate(lines):
				if '$' in line and price == None:
					price = line[line.index('$'):]
				elif item_name.lower().strip() in line.lower() and title == None:
					title = line
					volume = lines[index + 1]
					meat_produce_volume = lines[index + 2]


			if '/' in volume:
				volume_details = volume.split(' ')
				price_per_unit = volume_details[0]
				volume = meat_produce_volume[meat_produce_volume.index(' '):meat_produce_volume.index('/')].strip()
			else:
				price_per_unit = price + ' / ' + volume

			print("PRICE: ", price)
			print("TITLE: ", title)
			print("VOLUME: ", volume)
			print("PPUNIT: ", price_per_unit)
			print('\n\n')
		await browser.close()

asyncio.run(scrape('eggs', 47906))
asyncio.run(scrape('milk', 47906))
asyncio.run(scrape('chicken', 47906))
