#!pip install mkwikidata
import mkwikidata
from string import Template
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from rdflib import Graph, URIRef, Literal, RDF, FOAF
import csv
import io

class WikiPandas():
    def __init__(self, thisformat='json', debug=False):
        self.debug = debug
        self.format = thisformat
        self.state = 'default'
        self.data_list = []
        self.URIs = {}
        
    def add_lang(self, data):
        langdata = []
        for item in data:
            if 'xml:lang' not in item['value']:
                item['value']['xml:lang'] = ''
            langdata.append(item)
        return langdata
    
    def set_state(self, newstate):
        self.state = newstate
        return self.state

    def get_wikipedia_page(self, json_data, language='en'):
       try:
           sorted_data = dict(sorted(json_data.items(), key=lambda item: item[1], reverse=True))
           return {'identifier': list(sorted_data.keys())[0], "wiki": "https://%s.wikipedia.org/wiki/%s" % (language, list(sorted_data.keys())[0]) } 
       except:
           return
    
    def wikidata_locations(self, wdt = "P279*", wd = "Q515", location=None):
        if location:
            query = """
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/> 
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?cityLabel ?population ?gps
        WHERE
        {
          ?city wdt:P31/wdt:%s wd:%s .
          ?city wdt:P1082 ?population .
          ?city wdt:P625 ?gps .
          ?city rdfs:label "%s"@en .
          SERVICE wikibase:label {
            bd:serviceParam wikibase:language "en" .
          }
        }
        ORDER BY DESC(?population) LIMIT 100
        """ % (wdt, wd, location)
        else:
            query = """
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/> 
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?cityLabel ?population ?gps
        WHERE
        {
          ?city wdt:P31/wdt:%s wd:%s .
          ?city wdt:P1082 ?population .
          ?city wdt:P625 ?gps .
          SERVICE wikibase:label {
            bd:serviceParam wikibase:language "en" .
          }
        }
        ORDER BY DESC(?population) LIMIT 100
        """ % (wdt, wd)
        print(query)
        query_result = mkwikidata.run_query(query, params={ })
        if self.format == 'json':
            return query_result
        if self.format == 'pandas':
            data = [{"name" : x["cityLabel"]["value"], "population" : int(x["population"]["value"])} for x in query_result["results"]["bindings"]]
            df = pd.DataFrame(data).set_index("name")
            return df
        return

    def wikidata_entities(self, entityID="59269465", format='json'):
        query = """
        SELECT ?entity ?property ?propertyLabel ?value ?valueLabel
        WHERE {
          VALUES ?entity { wd:%s }
          ?entity ?property ?value.
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
        ORDER BY ?entity ?propertyLabel
        """ % entityID
        try:
            query_result = mkwikidata.run_query(query, params={ })
        except:
            return

        if format == 'json':
            return query_result
        if format == 'pandas':
            langdata = self.add_lang(query_result["results"]["bindings"])
            data = [{"property" : x["property"]["value"], "value" : str(x["value"]["value"]), "lang": str(x["value"]["xml:lang"])} for x in langdata]
            df = pd.DataFrame(data).set_index("property")
            return df
        return
    
    def viaf_to_wikidata(self, wdt="P214", viafID=None): 

        query = """
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX viaf: <http://viaf.org/viaf/>

       SELECT ?entity ?property ?propertyLabel ?value ?valueLabel
        WHERE {
          VALUES ?value { viaf:%s }.
          ?entity wdtn:%s ?value.
          ?entity ?property ?value.
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
        ORDER BY ?entity ?propertyLabel
        """ % (viafID, wdt)
        print(query)
        try:
            query_result = mkwikidata.run_query(query, params={ })
            if self.format == 'json':
                return query_result
            if self.format == 'pandas':
                langdata = self.add_lang(query_result["results"]["bindings"])
                data = [{"property" : x["property"]["value"], "value" : str(x["value"]["value"]), "lang": str(x["value"]["xml:lang"])} for x in langdata]
                df = pd.DataFrame(data).set_index("property")
                return df
            return
        except:
            return

    def wiki_generic(self, value, property=None, DEBUG=False):
        query = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?person ?personLabel ?property ?propertyLabel ?value ?type WHERE {
  ?person rdfs:label "%s"@en;
          wdt:P31 ?type;               # Ensuring it's a human (Q5)
          ?property ?value.
  
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
  }
}
        """ % (value)
        query_result = mkwikidata.run_query(query, params={ })
        self.format = 'json'
        if self.format == 'json':
            return query_result
        return

    def wikidata_persons(self, wdt="P214", personID="\"59269465\""):
        query = """
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/> 
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?person ?personLabel ?property ?propertyLabel ?value WHERE {  
          ?person wdt:%s %s.
          ?person ?property ?value.
          SERVICE wikibase:label {
            bd:serviceParam wikibase:language "en" .
          }
        }
        """ % (wdt, personID)
        query_result = mkwikidata.run_query(query, params={ })
        if self.format == 'json':
            return query_result
        if self.format == 'pandas':
            langdata = self.add_lang(query_result["results"]["bindings"])
            data = [{"property" : x["property"]["value"], "value" : str(x["value"]["value"]), "lang": str(x["value"]["xml:lang"])} for x in langdata]
            df = pd.DataFrame(data).set_index("property")
            return df
        return
    

    def get_wikidata_ids_from_wikipedia_page(self, page_title, language='eu'):
        if isinstance(page_title, list):
            page_titles = page_title 
        else:
            page_titles = [ page_title ]
    
        pageids = {}
        for page in page_titles:
            pageitems = {}
            if 'http' in page:
                if '//wikipedia' in page:
                    langcheck = re.search(r'wikipedia.org\/wiki\/(\S+)', page)
                    if langcheck:
                        pageitems['page'] = langcheck.group(1)
                        pageitems['lang'] = 'eu'               
                else:
                    page = page.replace('www.','')
                    langcheck = re.search(r'\/\/(\S+?)\.wikipedia.org\/wiki\/(\S+)', page)
                    if langcheck:
                        pageitems['page'] = langcheck.group(2)
                        pageitems['lang'] = langcheck.group(1)
            if pageitems:
                # Construct the URL for the Wikidata API request
                api_url = "https://www.wikidata.org/w/api.php"
                params = {
                    "action": "wbgetentities",
                    "sites": f"{pageitems['lang']}wiki",
                    "titles": pageitems['page'],
                    "format": "json",
                }

                # Make the API request
                response = requests.get(api_url, params=params)
                wikidata = response.json()
                wikientities = wikidata.get("entities")
                if wikientities:
                    entity_id = next(iter(wikientities))
                    pageids[page] = wikientities[entity_id].get("id")
        return pageids
    
    def wikipedia_to_wikidata(self, wikipedia_url, wikiuri: None, exportformat='json'):
        if not wikiuri:
            if 'wikipedia.org' in wikipedia_url:
                wikiuri = re.sub('^\S+wikipedia.org','',wikipedia_url)
            else:
                wikiurl = wikipedia_url
        response = requests.get(wikipedia_url)
        soup = BeautifulSoup(response.text, "html.parser")
        entities = {}
        links = {}
        wiki = []
        images = {}
        graph = Graph()

        # Define a namespace for FOAF (Friend of a Friend) vocabulary
        FOAF_NS = FOAF
        filters = "Wikipedia:" #|Help:Contents"
        for a in soup.find_all("img"):
            if 'upload.wikimedia.org' in str(a):
                if not '.svg' in str(a):
                    if not 'http' in a['src']:
                        if not wikipedia_url in images:
                            images[wikipedia_url] = "http:%s" % a['src']
        print(images)
        for a in soup.find_all("a", href=True):
            entities = {}
            if a["href"]:
                link = a['href']
                if not 'http' in link:
                    link = "https://wikipedia.org%s" % link
        
                linktitle = a.get_text()
                if '/wiki/' in link:
                    checkwikifilter = False
                    thiswikiuri = re.sub('^\S+wikipedia.org','', link)
                    if wikiuri in thiswikiuri:
                        checkwikifilter = True
                    else:
                        checkwikifilter = re.search(r'Wikipedia:|Help:|Special:|Portal:|Talk:|Privacy_policy|Main_Page|Template|Template_talk|erms_of_Use', link)
                    if not checkwikifilter:
                        if not 'Category' in link:
                            linktype = 'concept'
                            entities[link] = linktitle 
                            graph.add((URIRef(link), RDF.type, FOAF.Person))
                            graph.add((URIRef(link), FOAF.name, Literal(a.get_text())))
                            if self.state == 'linking':
                                wikiinfo = self.get_wikidata_ids_from_wikipedia_page(link)
                                if wikiinfo:
                                    wikiID = wikiinfo[link]
                                else:
                                    wikiID = ''
                                entities = { 'wikilink': link, 'value': linktitle, 'type': linktype, 'wikiID': wikiID }
                            else:
                                entities = { 'wikilink': link, 'value': linktitle, 'type': linktype, 'wikiID': '' }
                        else:
                            links[link] = linktitle
                            linktype = 'category'
                            entities = { 'wikilink': link, 'value': linktitle, 'type': linktype, 'wikiID': '' }
                        if not entities in wiki:
                            wiki.append(entities)
        if exportformat == 'json':
            return { 'entities': wiki, 'image': images }
        if self.debug:
            print(wiki)
        if exportformat == 'pandas':
            if self.state == 'linking':
                data = [{"property" : x["wikilink"], "value" : str(x["value"]), "type": str(x['type']), "wikiID": x['wikiID']} for x in wiki]
            else:
                data = [{"property" : x["wikilink"], "value" : str(x["value"]), "type": str(x['type'])} for x in wiki]
            df = pd.DataFrame(data).set_index("property")
            return df

    def run_query(self, query, params={}, service_url=None):
        outputformat = 'Accept: text/tab-separated-values'
        headers = {
            #'Accept': 'application/sparql-results+json',
            'Accept': 'text/tab-separated-values',
            'Content-type': 'application/sparql-query'
        }
        if service_url is None:
            service_url = 'https://query.wikidata.org/sparql'

        query_template = Template(query)
        execute_query = query_template.substitute(**params)
        r = requests.post(service_url, params={'format': 'json', 'query': query}, data=query, headers=headers)
        response = r.text #json()
        if response:
             tsvfile = io.StringIO(response)
             reader = csv.DictReader(tsvfile, delimiter='\t', fieldnames=["element", "personLabel", "property", "propertyLabel", "value", "type"])

             for row in reader:
                 self.data_list.append(row)
                 if 'label' in row['property'] and '@en' in row['value']:
                     if self.debug:
                         print(row['value'], row['property'])
                 if 'http' in row['element']:
                     self.URIs[row['element']] = row['value']
        return response
