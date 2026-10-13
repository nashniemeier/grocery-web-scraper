import asyncio
import nodriver as uc

async def main():
	browser = await uc.start()

	page = await browser.get('https://www.walmart.com/search?q=chicken')

	print("Waiting 5 seconds before refresh...")
	await page.sleep(5)

	print("Refreshing page...")
	await page.reload()

	print("Waiting 5 seconds for items to populate...")
	await page.sleep(5)

	await page.evaluate("""
                () => {
                        const sponsoredSpotlights = document.querySelectorAll(
                                'div[id*="spotlight"], div[aria-label*="Sponsored"], div[data-testid*="spotlight"]'
                        );
                        sponsoredSpotlights.forEach(el => el.remove());
                }
        """)

	# 1. Begins scraping

	products = await page.select_all(
		'[data-test-id="gpt-product-descriptive-meta-data-container"]'
	)

	count = 0
	for product in products:

		# Skip sponsored products
		sponsored = await product.query_selector(
			'[data-test-id="gpt-sponsored-tag-container"]'
		)

		if sponsored:
			continue

		# Get product title
		title = await product.query_selector(
			'[data-automation-id="product-title"]'
		)

		# Get price information
		price_info = await product.query_selector(
			'[data-testid="unified-global-product-price-a11y-text"]'
		)

		if title and price_info:
			title_text = title.text
			price_text = price_info.text

			price_text = price_text.replace("Final cost by weight", "")
			price_text = price_text.replace(" ¢", "¢")
			price_text = price_text.replace("fl oz", "fl.oz")
			price_text = price_text.strip()

			price_per_unit = ""
			total_price = ""

			price_details_arr = price_text.split(" ")
			print(price_details_arr)

			if '/' not in price_text:
				price_per_unit = "N/A"
			else:
				# Get the price per unit given by walmart
				price_per_unit = price_details_arr[-1]

			for item in price_details_arr:
				if '$' in item:
					total_price = item
					break


			item_details = {
					"TITLE": title_text,
					"PPUNIT": price_text,
					"PRICE": total_price,
					"PRICE_NUM": float(total_price[1:])
			}

			print("TITLE:", title_text)
			print("PRICE INFO:", price_text)
			print("PPUNIT:", price_per_unit)
			print("PRICE:", total_price)
			print("PRICE_NUM:", item_details["PRICE_NUM"])
			print()

			if count > 5:
				break
			count += 1

	await browser.stop()

if __name__ == '__main__':
	uc.loop().run_until_complete(main())
