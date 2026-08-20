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

		# Now get the products
		card_locator = page.locator('li[class="ColListing--__sc-176c0200-13 lkSbvF"]')
		await card_locator.nth(4).wait_for(state='visible', timeout=15000)

		#await page.wait_for_timeout(2000)

		print("We have the card locator")

		await page.wait_for_timeout(2000)
		cards = await card_locator.all()
		print(f'Found {len(cards)} products.')
		parsed_products = []

		for card in cards[:5]:

			# Grab all text
			full_text = await card.inner_text()

			lines = [line.strip() for line in full_text.split('\n') if line.strip()]
			#print(lines)
			print('\n\n')

			#product_url = await card.get_attribute('href')
			#img_el = card.locator('img').first
			#img_url = await img_el.get_attribute('src') if await img_el.count() > 0 else None

			# lines[0] is always Title - Volume, Price
			details = lines[0].replace(' - ', ',').split(',')

			title = details[0]
			volume = details[1]
			price = details[2]

			print(details)

			volume_count = volume[:volume.index(' ')]
			unit = volume[volume.index(' '):].strip()
			total_price = price[2:price.index('.')] + price[price.index('.'):(price.index('.') + 3)]

			per_unit = round((float(total_price) / float(volume_count)), 2)
			print(str(per_unit) + '/' + unit)




asyncio.run(scrape('Chicken', 46259))
