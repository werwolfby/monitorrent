import urllib3
from urllib3.util import Url
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio


def main():
    req_headers, new_cookies = asyncio.run(solve_challenge("https://www.lostfilm.tv"))
    print(req_headers)
    print(new_cookies)


async def solve_challenge(url, timeout=120000):
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(record_har_path="challenge.har")
        page = await context.new_page()

        req_headers = {}

        async def on_request(req):
            all_headers = await req.all_headers()
            nonlocal req_headers
            req_headers['User-Agent'] = all_headers['user-agent']

        page.on('request', on_request)

        await page.goto(url)

        features = [
            asyncio.create_task(wait_for_page_input(page, timeout=timeout)),
            asyncio.create_task(wait_for_iframe_input(page, timeout=timeout)),
            asyncio.create_task(page.wait_for_selector('.left-side > .menu', timeout=timeout)),
        ]

        done, rest = await asyncio.wait(features, return_when=asyncio.FIRST_COMPLETED)

        if features[-1] not in done:
            await features[-1]

        for task in rest:
            try:
                task.cancel()
            except asyncio.CancelledError:
                pass

        url_parse: Url = urllib3.util.parse_url(url)
        new_cookies = {}
        while 'cf_clearance' not in new_cookies:
            page_cookies = await context.cookies(url_parse.scheme + "://" + url_parse.hostname)
            new_cookies = {k['name']: k['value'] for k in page_cookies if k['name'] in ['cf_clearance']}

        await context.close()
        await browser.close()

        return req_headers, new_cookies


async def wait_for_iframe_input(page, timeout=120000):
    try:
        await page.frame_locator("iframe").locator("input").click(timeout=timeout)
    except asyncio.CancelledError:
        pass
    except:
        pass


async def wait_for_page_input(page, timeout=120000):
    try:
        await page.locator('input[type="button"]').click(timeout=timeout)
    except asyncio.CancelledError:
        pass
    except:
        pass


if __name__ == "__main__":
    main()
