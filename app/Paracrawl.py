import asyncio
import nest_asyncio
import re
import os
import async_timeout
import aiohttp

# Allow nested event loops in environments like Jupyter Notebooks
nest_asyncio.apply()
class Paracrawl():
    def __init__(self, query, dataverses, debug=False):
        self.content = {}
        self.roots = dataverses
        self.query = query
        self.run()
        
    async def fetch(self, session, url):
        """Fetch a page's content with a timeout."""
        try:
            with async_timeout.timeout(10):  # Timeout for the request
                async with session.get(url) as response:
                    print(f"Fetching {url}")
                    return await response.text(), response.status
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None, None

    async def crawl(self, urls):
        """Crawl multiple URLs in parallel."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    def get_urls(self):
        self.urls = []
        for url in self.roots:
            self.urls.append("%s/api/search?q=%s" % (url, self.query))
        return self.urls

    def run(self):
        urls = self.get_urls()
        results = asyncio.run(self.crawl(urls))

        # Print results
        for idx, (content, status) in enumerate(results):
            if content:
                self.content[urls[idx]] = content #[:200]
        return len(self.content)
