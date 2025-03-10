import asyncio  # noqa F401
import bs4
import yaml
import sys

from playwright.async_api import async_playwright
from tqdm import tqdm
from urllib.parse import urlparse


def is_valid_link(link):
    link = link.lower()
    return (".pdf" in link or ".doc" in link) and ("mailto" not in link)


async def get_support_info_links(doi_list):
    links = {}
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        for doi in tqdm(doi_list):
            try:
                page = await browser.new_page()
                if doi.startswith("10.1016"):
                    await page.goto(f"https://doi.org/{doi}", wait_until="networkidle")

                    all_links = await page.eval_on_selector_all(
                        "a[href]",  # Select all links
                        "elements => elements.map(e => e.href)",
                    )
                    valid_links = [
                        link
                        for link in all_links
                        if link.endswith((".pdf", ".doc", ".docx")) and "?" not in link
                    ]
                    links[doi] = tuple(set(valid_links))
                else:
                    if doi.startswith("10.31635"):
                        await page.goto(f"https://www.chinesechemsoc.org/doi/suppl/{doi}")
                    else:
                        await page.goto(f"https://doi.org/{doi}")
                    content = await page.content()
                    soup = bs4.BeautifulSoup(content, "html.parser")
                    all_hrefs = [
                        link["href"] for link in soup.find_all("a") if "href" in link.attrs
                    ]
                    hrefs = list(filter(is_valid_link, all_hrefs))
                    url = urlparse(page.url)
                    links[doi] = tuple(
                        {
                            (
                                href
                                if href.startswith("http")
                                else f"{url.scheme}://"
                                + f"{url.netloc}/{href}".replace("//", "/")
                            )
                            for href in hrefs
                        }
                    )
                await page.close()
            except Exception:
                links[doi] = tuple()
            print(doi, links[doi])

        await browser.close()
    return links


if __name__ == "__main__":
    if len(sys.argv) > 1:
        start, end = map(int, sys.argv[1:])
    else:
        start, end = 0, None
    refs = sorted(open("all_reference_dois.txt").read().splitlines())
    links = asyncio.run(get_support_info_links(refs[start:end]))
    name = "support_info_links" + (
        "" if end is None else f"_{start}_{end}"
    )
    with open(f"{name}.yaml", "w") as f:
        yaml.safe_dump(links, f)

    print("Done")
