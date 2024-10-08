import asyncio
import nest_asyncio
import re
import os
import async_timeout
import aiohttp
import json
from .utils import linked_data_query_constructor, get_doi_from_text
from .config import config
from .AI import AIMaker
from .GraphQuery import GraphQuery
from .Attention import Attention
import logging
from urllib.parse import urlparse

# Allow nested event loops in environments like Jupyter Notebooks
nest_asyncio.apply()
class Paracrawl():
    def __init__(self, prompt, dataverses, reasoning=None, directquery=None, debug=False):
        self.DEBUG = debug
        self.content = {}
        self.strategy = 'STRICT'
        self.smartquery = {'searchquery': ''}
        self.roots = dataverses
        self.timeout = 10
        if reasoning:
            self.reasoning = reasoning
        else:
            self.reasoning = os.environ['REASONING']

        if directquery:
            self.query = directquery
        else:
#            try:
             self.query = self.smartprompt("<TEXT> %s </TEXT>" % prompt)['searchquery']
#            except:
#                self.query = ''
        self.run()
        self.results = []
        self.reader()
        
    async def fetch(self, session, url):
        """Fetch a page's content with a timeout."""
        try:
            with async_timeout.timeout(int(self.timeout)):  # Timeout for the request
                async with session.get(url, ssl=False) as response:
                    #print(f"Fetching {url}")
                    return await response.text(), response.status
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            with open("%s/error.log" % os.environ['DATADIR'], "w") as file:
                file.write(urlparse(url).hostname) 
            return None, None

    async def crawl(self, urls):
        """Crawl multiple URLs in parallel."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    def get_urls(self):
        self.urls = []
        for url in self.roots:
            self.q = self.query
            self.q = self.q.replace(' ','%20')
            self.urls.append("%s/api/search?q=%s" % (url, self.q))
        print("Total: %s" % len(self.urls))
        logging.info(self.urls)
        return self.urls

    def reader(self):
        for url in self.content:
            print(url)
            content = self.content[url]
            #print(content)
            #if 'items' in content['data']:
            try:
                for item in content['data']['items']:
                    if 'citationHtml' in item:
                        thisdoi = get_doi_from_text(item['citationHtml'])
                        if thisdoi:
                            html =  "<b><a href='/?url=%s'>[ Chat ]</a></b>&nbsp;%s" % ("http://" + thisdoi, item['citationHtml']) 
                            self.results.append(html)
                    else:
                        if 'dataset_citation' in item:
                            html = "<b><a href='/?url=%s'>[ Chat ]</a></b>&nbsp;%s" % ("http://%s" % item['dataset_persistent_id'], item['dataset_citation'])
                            self.results.append(html)
            except:
                return
        return

    def run(self):
        urls = self.get_urls()
        results = asyncio.run(self.crawl(urls))

        # Print results
        for idx, (content, status) in enumerate(results):
            try:
                if content:
                    self.content[urls[idx]] = json.loads(content) #[:200]
            except:
                continue
        return len(self.content)

    def parse_string_to_dict(self, var):
        """
        Parse a multi-line formatted string and extract key-value pairs into a dictionary.

        Args:
            var (str): The input string to parse.

        Returns:
            dict: A dictionary containing the parsed key-value pairs.
        """
        result = {}

        # Split the input string into lines and process each line
        for line in var.strip().splitlines():
            # Split each line into key and value parts by the first occurrence of ':'
            if ':' in line:
                key, value = line.split(':', 1)  # Split only on the first ':'
                key = key.strip()                # Remove any leading/trailing spaces from the key
                value = value.strip()            # Remove any leading/trailing spaces from the value

                # If the value contains a comma, convert it into a list of values
                if ',' in value:
                    value = [v.strip() for v in value.split(',')]

                forbidden = ['data', 'dataset', 'datasets']
                if type(value) == list:
                    for v in value:
                        if not v in result:
                            if len(key) > 2 and not key in forbidden:
                                result[v] = key.lower()
                else:
                    if value and key:
                        result[value] = key.lower()
                #if 'locations' in result:
                #    result['keywords'].pop(result['locations'], None)
                print(json.dumps(result))

        return result

    def smartprompt(self, prompt):
        logging.info("smartprompt")
        qa = prompt
        self.ai = AIMaker(config, LLAMA_URL=os.environ['OLLAMA'].replace('http://',''), debug=True)
        language = "English"
        newrole = "search expert specializing in search engines."
        focus = "classification of under 3 different intent categories:  transactional, navigational, informational. Informational search queries: in these instances, the user is looking for certain information for example, “how to make coffee”, avigational search queries: these requests establish that the user wants to visit a specific site or find a certain vendor– for example, “YouTube” or “Apple”."
        logging.debug("This is a debug message: %s", focus)
        self.ai.changefocus(focus)
        newrole = "classification model"
        self.ai.changerole(newrole)
        category = "informational"
        keywords = {"second world war": "keyword", "Ukraine": "location", "data": "keyword"}
        year = "2024"

        exampleJSON = f"""
        {{
    "@context": {{
        "classification": "https://schema.org/Thing",
        "keywords": "https://schema.org/keywords",
        "synonyms": "https://schema.org/sameAs",
        "country": "https://schema.org/Country",
        "locations": "https://schema.org/Location",
        "period": {{
            "@id": "https://schema.org/TimePeriod",
            "@type": "https://schema.org/Date"
        }},
        "searchquery": "https://schema.org/SearchAction",
        "person": "https://schema.org/Person",
        "organization": "https://schema.org/Organization",
        "alternativeLocation": "https://schema.org/Place"
    }},
          "@type": "Thing",
          "classification": "{category}",
          "keywords": {json.dumps(keywords)},
          "synonyms": "{{ [synonym1, synonym2] }}",
          "locations": "{{ [location1, location2, location3] }},
          "country": "{{ country }},
          "period": "{{'startyear': year, 'endyear': year}}"
        }}
        """
        example = f""" in CVS format:
        locations: location1, location2, location3
        keywords: keyword1, keyword2, keyword3
        date: 2013
        question: keyword1, keyword2
        """

        languages = "in English"
        newprompt = f"You are %%role%%. Your task is to use %%focus%% and classify <TEXT> and </TEXT> in %%message%%. Return the classification and list of keywords exactly like in this structure {example} without giving any extra explanation. For each \"keywords\" field, provide up to 10 synonyms in {languages}, put city or local region in \"locations\" field including country if there is some location mentioned (include this location), make prediction on the period with dates only if present. Put in \"question\" field only main keywords extracted from input."  # Don't mention yourself as %%role%%."
        #print(newprompt)
        #self.ai.changeprompt(newprompt)
        #annotr = self.ai.llama3(prompt).replace("As a %s, " % newrole, '')

        ner = {}
        if self.reasoning == 'llama':
            attention = Attention(LLAMA_URL=os.environ['OLLAMA'].replace('http://',''))
            attention.changequestion(qa)
            ner = {}
            #ner = { 'netherlands': 'locations' }
            for keyword in attention.keywords: 
                if len(keyword.split(' ')) > 1:
                    ner[keyword] = 'keywords'

        if self.reasoning == 'spacy':
            attention = Attention()
            entities = attention.analyze_question(qa)
            ner = attention.form_ner_report(entities)

        #print(annotr)
        #print('***')
        #q = linked_data_query_constructor(annotr)
        #ner = self.parse_string_to_dict(annotr)
        print(ner)
        g = GraphQuery(ner)
        # Generate and print the Solr query from the graph
        solr_query = g.generate_solr_query()
        print(solr_query)
        if solr_query:
            q = {'searchquery': solr_query }
            #q = {}
            #for item in ner:
            #    if ner[item] == 'question':
            #        q = {'searchquery': item } 
            self.smartquery = q
            return q

        searchquery = ''
        forbidden = ['dataset', 'data']
        if 'keywords' in q:
            searchquery = ''
            for keyword in q['keywords']:
                print("KKK %s " % keyword)
                if searchquery:
                    qkeyword = keyword
                    if ' ' in keyword:
                        qkeyword = "\"%s\"~3 " % keyword
                    if not 'data' in qkeyword.lower():
                        thisoperator = 'OR' 
                        if qkeyword.isdigit():
                            thisoperator = 'AND'
                        searchquery = "%s %s title:%s" % (searchquery, thisoperator, qkeyword)
                else:
                    qkeyword = keyword
                    if ' ' in keyword:
                        qkeyword = "\"%s\"~3" % keyword
                    if not 'data' in qkeyword.lower(): 
                        searchquery = "title:%s" % qkeyword
            if searchquery:
                q['searchquery'] = searchquery
        self.smartquery = q
        return q
