import asyncio
from playwright.async_api import async_playwright, Playwright
from urllib.parse import quote

async def scrape(item_name, zipcode):
	async with async_playwright() as p:

		base_url ='https://ww2.freshthyme.com/sm/planning/rsid/201/results?q='
		url = base_url + quote(item_name)

		# Start up playwright for our page
		browser = await p.chromium.launch(headless=False)
		page = await browser.new_page()
		await page.goto(url)

		# Changing the store
		await page.locator('button[id="StoreHeaderButton"]').click()
		await page.get_by_role('button', name='Change Store').click()
		await page.get_by_label('Location').fill(str(zipcode))
		await page.locator('div[role="option"]').first.wait_for(state='visible')
		await page.locator('button[aria-label="Submit search"]').click()
		await page.wait_for_timeout(2000)

		switch_btn = page.locator('button[class="Button--__sc-cc8561e3-0 SecondaryButton--__sc-cc8561e3-11 eXeAcb elxxxt SelectStoreButton--__sc-5c4b63ea-0 ePEJlt"]')

		# Determine if we default to the closest store
		switch_btn_text = await switch_btn.first.inner_text()
		if switch_btn_text == "Your Active Store":
			await page.locator('button[aria-label="Close  modal"]').click()
		else:
			await switch_btn.first.click()

		await page.wait_for_timeout(100000)

		# Now get the products
		await card_locator = page.locator('.ProductCard--__sc-48568d95-0 dpzklt')
		await card_locator.nth(4).wait_for(state='visible', timeout=15000)

		await page.wait_for_timeout(2000)
		await cards = card_locator.all()
		print(f'Found {len(cards)} products.')
		parsed_products = []

		for card in cards:

			# Grab all text
			full_text = await card.inner_text()

			# Split into individual lines
			lines = [line.strip() for line in full_text.split('\n') if line.strip()]

			product_url = await card.get_attribute('href')
			img_el = card.locator('img').first
			img_url = await img_el.get_attribute('src') if await img_el.count() > 0 else None

			unit_price = pkg_weight = stock_status = display_price = title = None


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




	run(playwright, 'rice', 46259)

asyncio.run(scrape('chicken', 46259))
