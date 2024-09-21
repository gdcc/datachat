import asyncio
import nest_asyncio
import re
import os
import async_timeout
import aiohttp
import json
from utils import linked_data_query_constructor
from config import config
from AI import AIMaker

# Allow nested event loops in environments like Jupyter Notebooks
nest_asyncio.apply()
class Paracrawl():
    def __init__(self, prompt, dataverses, directquery=None, debug=False):
        self.DEBUG = debug
        self.content = {}
        self.smartquery = ''
        self.roots = dataverses
        if directquery:
            self.query = directquery
        else:
            self.query = self.smartprompt(prompt)['searchquery']
        self.run()
        self.results = []
        self.reader()
        
    async def fetch(self, session, url):
        """Fetch a page's content with a timeout."""
        try:
            with async_timeout.timeout(10):  # Timeout for the request
                async with session.get(url) as response:
                    #print(f"Fetching {url}")
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

    def reader(self):
        for url in self.content:
            print(url)
            content = self.content[url]
            #print(content)
            if 'items' in content['data']:
                for item in content['data']['items']:
                    if 'citationHtml' in item:
                        self.results.append(item['citationHtml'])
        return

    def run(self):
        urls = self.get_urls()
        results = asyncio.run(self.crawl(urls))

        # Print results
        for idx, (content, status) in enumerate(results):
            if content:
                self.content[urls[idx]] = json.loads(content) #[:200]
        return len(self.content)

    def smartprompt(self, prompt):
        self.ai = AIMaker(config, LLAMA_URL=os.environ['OLLAMA'].replace('http://',''), debug=True)
        language = "English"
        newrole = "search expert specializing in search engines."
        focus = "classification of under 3 different intent categories:  transactional, navigational, informational. Informational search queries: in these instances, the user is looking for certain information for example, “how to make coffee”, avigational search queries: these requests establish that the user wants to visit a specific site or find a certain vendor– for example, “YouTube” or “Apple”."
        self.ai.changefocus(focus)
        newrole = "classification model"
        self.ai.changerole(newrole)
        category = "informational"
        keywords = ["second world war", "Ukraine", "data"]
        year = "2024"

        example = f"""
        {{
          "classification": "{category}",
          "keywords": {json.dumps(keywords)},
          "synonyms": "{{ [synonym1, synonym2] }}",
          "country": "{{ country1, country2 }},
          "period": "{{'startyear': year, 'endyear': year}}"
        }}
        """
        newprompt = f"You are %%role%%. Your task is to use %%focus%% and classify <TEXT> and </TEXT> in %%message%%. Return the classification and list of keywords in this structure {example} without giving any extra explanation. For each \"keyword\", provide up to 10 synonyms in English and Dutch, put predicated geolocations in \"country\", make prediction on the period with dates."  # Don't mention yourself as %%role%%."
        self.ai.changeprompt(newprompt)
        annotr = self.ai.llama3(prompt).replace("As a %s, " % newrole, '')
        q = linked_data_query_constructor(annotr)
        searchquery = ''
        forbidden = ['dataset', 'data']
        if 'keywords' in q:
            searchquery = ''
            for keyword in q['keywords']:
                if searchquery:
                    qkeyword = keyword
                    if ' ' in keyword:
                        qkeyword = "\"%s\"~3 " % keyword
                    if not 'data' in qkeyword.lower():
                        searchquery = "%s OR %s" % (searchquery, qkeyword)
                else:
                    qkeyword = keyword
                    if ' ' in keyword:
                        qkeyword = "\"%s\"~3" % keyword
                    if not 'data' in qkeyword.lower(): 
                        searchquery = qkeyword
            if searchquery:
                q['searchquery'] = searchquery
        self.smartquery = q
        return q
