import asyncio
from playwright.async_api import async_playwright, Playwright
from urllib.parse import quote

testing = True

async def scrape(item_name, zipcode):
	async with async_playwright() as playwright:
		# Start up playwright for our page
		start_url = "https://www.aldi.us/store/aldi/s?k="
		browser = await playwright.chromium.launch(headless=False)
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
		await page.get_by_role('button', name='Change store').first.click()

		# Entering the zipcode
		await page.locator('.e-1wlht9u').click()
		await page.locator('.e-t267xt').fill(str(zipcode))
		await page.locator('.e-616lx5').click()

		# Selecting the store, picking the first one that shows up
		await page.locator('.e-5irn7x').first.click()
		await page.get_by_role('button', name='Shop this store').click()

		# Getting item cards
		card_locator = page.locator('a[data-item-card-button="true"]')
		await card_locator.first.wait_for(state='visible', timeout=15000)

		await page.wait_for_timeout(2000)
		cards = await card_locator.all()

		# End of playwright commands
		print(f'Found {len(cards)} products.')
		parsed_products = []

		# Extract information
		for card in cards:

			# Grab all text
			full_text = await card.inner_text()
			
			# Split into individual lines
			lines = [line.strip() for line in full_text.split('\n') if line.strip()]

			product_url = await card.get_attribute('href')
			img_el = card.locator('img').first
			image_url = await img_el.get_attribute('src') if  await img_el.count() > 0 else None

			unit_price = None
			pkg_weight = None
			stock_status = None
			display_price = None
			title = None

			for line in lines:
				if "/ lb" in line or "/ oz" in line:
					unit_price = line
				elif "lb / package" in line or "oz / package" in line:
					pkg_weight = line
				elif "stock" in line.lower():
					stock_status = line
				elif line.startswith("$") and not display_price:
					display_price = (line[:-2] + '.' + line[-2:])
				elif item_name.lower() in line.lower():
					title = line

			item_data = {
				"title": title,
				"display_price": display_price,
				"unit_price": unit_price,
				"package_weight": pkg_weight,
				"stock_status": stock_status,
				"product_url": product_url,
				"image_url": image_url,
				"raw_text_lines": lines
			}

			parsed_products.append(item_data)
		
		count = 0

		for item in parsed_products:
			join = " ".join(item["raw_text_lines"])
			if item_name.lower() in join.lower():

				count += 1

				print(item["title"])
				print(item["display_price"])
				print(item["package_weight"])
				if item["raw_text_lines"]:
					print(item["raw_text_lines"])
				print('\n')
			if count == 5:
				break
				print('\n')

asyncio.run(scrape('chicken', 46259))
