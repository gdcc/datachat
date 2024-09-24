#from telethon import TelegramClient, events, sync
from NowMuseum import NowMuseum
#from telethon.tl.functions.messages import GetHistoryRequest
import json
from elasticsearch import Elasticsearch
import arrow
import re
import textwrap
from datetime import datetime, date, timedelta
import pytz
import textwrap
from calendar import timegm
from textblob import TextBlob
import langid
import requests, json, io, sys
import random
from time import sleep
import hashlib

class AIMaker():
    def __init__(self, config, LLAMA_URL, defaultmodel="llama3", defaultrole="traveller", focus='test', ingest=False, debug=False):
        self.config = config
        if 'ELASTIC' in config:
            self.elastic = Elasticsearch([config['ELASTIC']], http_auth=(config['HTTP_LOGIN'], config['HTTP_PASSWORD']), use_ssl=False, verify_certs=False, timeout=config['ELASTICTIMEOUT'])
        else:
            self.elastic = ''

        esconfig = {}
        esconfig['elastichost'] = config['ELASTIC']
        esconfig['elasticlogin'] = config['HTTP_LOGIN']
        esconfig['elasticpassword'] = config['HTTP_PASSWORD']
        esconfig['elasticport'] = config['ELASTICPORT']
        esconfig['elasticindex'] = config['INDEX']
        esconfig['elasticcollection'] = config['COLLECTION']
        self.mq = NowMuseum(esconfig)

        self.model = defaultmodel
        self.role = defaultrole
        self.focus = focus
        self.debug = debug
        self.LLAMA_URL = LLAMA_URL
        self.prompt = f"You are %%role%%, acting as an assistant on %%message%%. If required translate in English and rewrite the text as %%focus%% review."
        self.parameters = {
        'role': self.role,
        'message': 'message',
        'focus': self.focus
        }
        
        import hashlib

    def generate_unique_id(self, input_string, max_value=2**63-1):
        if input_string:
            # Create a hash object using SHA-256
            hash_object = hashlib.sha256(input_string.encode())
            # Convert the hash to a hexadecimal string
            hex_dig = hash_object.hexdigest()
            # Convert the hexadecimal string to an integer
            unique_id = int(hex_dig, 16)
            unique_id = unique_id % max_value
            return unique_id
        return

    def opendebug(self, status):
        self.debug = status
        return
        
    def replace_placeholders(self, text, **kwargs):
        for key, value in kwargs.items():
            placeholder = f"%%{key}%%"
            text = text.replace(placeholder, value)
        return text

    def updateprompt(self, text, message): #, **kwargs):
        self.parameters = {
        'role': self.role,
        'message': message,
        'focus': self.focus
        }
        return self.replace_placeholders(text, **self.parameters)
    
    def changemodel(self, thismodel):
        self.model = thismodel
        return
    
    def changeprompt(self, newprompt):
        self.prompt = newprompt
        return
    
    def changerole(self, newrole):
        self.role = newrole
        return
    
    def changefocus(self, newfocus):
        # example: travel
        self.focus = newfocus
        return

    def llama3(self, message):
        s = requests.Session()
        thisprompt = self.updateprompt(self.prompt, message) #, self.parameters)
        self.debug = True
        if self.debug:
            print("PROMPT %s: " % thisprompt)
        output=""
        with s.post("http://%s/api/generate" % self.LLAMA_URL, json={'model': self.model, 'prompt': thisprompt}, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    j = json.loads(line)
                    if "response" in j:
                        output = output +j["response"]
        return output

    def result_to_es(self, news, annotation=False, query=False, loc=False):
        DEPOSIT = False
        if 'DEPOSIT' in self.config:
            DEPOSIT = self.config['DEPOSIT']
        data = news['_source']
        print("RESULT")
        if not '_id' in news:
            news['_id'] = self.generate_unique_id(data['title'])
            #data['urlid'] = str(news['_id'])
        print("DATA %s" % data)
        print(self.config)

        if DEPOSIT:
            #print("Adding %s" % data['url'])
            if annotation:
                data['ai'] = annotation
            if query:
                data['query'] = query
            if loc:
                data['land'] = loc

            newindex = self.config['ANNOINDEX']
            newcollection = self.config['ANNOCOLLECTION']
            uid = news['_id']
            if data:
                try:
                    uid = news['_id']
                    self.elastic.create(index=newindex, doc_type=newcollection, body=data, id=uid)
                except:
                    self.elastic.delete(index=newindex, doc_type=newcollection, id=uid)
                    self.elastic.create(index=newindex, doc_type=newcollection, body=data, id=uid)
#        print(data)
        return data 

    def get_message_id(self, uid=False, search=False, checkanno=False):
        keywords = {}
        query = ''
        if uid:
            if 'http' in str(uid):
                query = "url:\"%s\"" % uid
            else:
                query = "urlid:\"%s\"" % uid

        if search:
            query = search

        keywords['keywords'] = "%s" % query
        index = self.config['INDEX']
        collection = self.config['COLLECTION']
        if checkanno:
            index = self.config['ANNOINDEX']
            collection = self.config['ANNOCOLLECTION']
        print(keywords['keywords'])
        print(self.config)
        # SOC_ES_INDEX SOC_ES_COLLECTION
        news = self.mq.get_news(keyword=keywords,
                                elastic=self.elastic,
                                index=index,
                                collection=collection)
        return news

    def get_anno_id(self, thisprompt): #, localconfig):
        keywords = {}
        if 'http' in thisprompt:
            query = "url:\"%s\"" % url
        else:
            query = thisprompt
        keywords['keywords'] = "%s" % thisprompt #query
        print(keywords['keywords'])
        # SOC_ES_INDEX SOC_ES_COLLECTION
        news = self.mq.get_news(keyword=keywords,
                                elastic=elastic,
                                index=self.config['ANNOINDEX'],
                                collection=self.config['ANNOCOLLECTION'])
        return news

    def record_exists(self, newsitem):
        if not newsitem:
            return False
        if not 'ai' in newsitem[0]['_source']:
            return False
        return True

    def word_frequency(self, text, word):
        # Convert both text and word to lowercase to make the search case-insensitive
        text = text.lower()
        pattern = r'[.,|?-]'
        replaced_text = re.sub(pattern, ' ', text)
        word = word.lower()

        # Split the text into words
        words = replaced_text.split()

        # Count the occurrences of the specific word
        frequency = words.count(word)

        return frequency

    def add_to_attention(self, thistext, attentiontexts):
        if thistext:
            if not thistext in attentiontexts:
                attentiontexts.append(thistext)
        return attentiontexts

    def attention(self, text, keyword, max_length=255, showsnippets=False):
        fr = self.word_frequency(text, keyword)
        if not showsnippets:
            print(fr)
            if fr > 1:
                return text
            elif not fr:
                return text

        # Split the text into sentences
        #sentences = text.split('. ')
        split_text = re.split(r'[.\n\t]', text)
        sentences = [s.strip() for s in split_text if s.strip()]

        # Filter sentences that contain the keyword
        #sentences_with_keyword = [s for s in sentences if keyword in s]
        sentences_with_keyword = []
        for uid in range(0, len(sentences)): 
            s = sentences[uid]
            p, n = '', ''
            if uid > 1:
                p = sentences[uid-1]
            if uid < len(sentences)-1:
                n = sentences[uid+1]
            if keyword.lower() in s.lower():
                sentences_with_keyword = self.add_to_attention(p, sentences_with_keyword)
                sentences_with_keyword = self.add_to_attention(s, sentences_with_keyword)
                sentences_with_keyword = self.add_to_attention(n, sentences_with_keyword)


        # Join sentences and wrap the text
        wrapped_text = textwrap.shorten('. '.join(sentences_with_keyword), width=max_length, placeholder="...")

        return wrapped_text

    def extract_classification_and_result(self, text):
        # Patterns to match classification and result
        classification_pattern = r'%%CLASSIFICATION:\s*(.*)'
        result_pattern = r'%%RESULT:\s*(.*)'
        classification_another_pattern = r'\*\s+Category\:\s*(.*)'

        # Extract classification
        classification_match = re.search(classification_pattern, text)
        classification = classification_match.group(1).strip() if classification_match else None
        if classification:
            classification = classification.replace('*','')
            if 'N/A' in classification:
                classification = 'Promotion'
        else:
            classification = 'Promotion'
        if not classification:
            classification_match = re.search(classification_another_pattern, text)
            classification = classification_match.group(1).strip() if classification_match else None
            if classification:
                classification = classification.replace(' Category: ','')

        # Extract result
        result_match = re.search(result_pattern, text)
        result = result_match.group(1).strip() if result_match else None
        if result:
            result = result.replace('*','')
        else:
            result = 'Neutral'
        return result, classification

    def issues_cleaner(self, problem):
        if not problem:
            return 
        noresult = ['No specific', 'csv', 'does not', 'text mentions', 'none', 'Based on']
        for testresult in noresult:
            if testresult.lower() in problem.lower():
                return
        if '->' in problem:
            p = problem.split('->')
            problem = p[0]
        if '/' in problem:
            p = problem.split('/')
            problem = p[0]
        if ';' in problem:
            p = problem.split(';')
            problem = p[0]
        if '-' in problem:
            p = problem.split('-')
            problem = p[0]
        if '>' in problem:
            p = problem.split('>')
            problem = p[0]
        if ',' in problem:
            p = problem.split(',')
            problem = p[0]
        if '(' in problem:
            p = problem.split('(')
            problem = p[0]
        if ')' in problem:
            p = problem.split(")")
            problem = p[0]
        if 'category' in problem.lower():
            problem = problem.replace('Category:', '')
        problem = problem.lower() #replace('issues', 'Issues')
        if not 'issues' in problem:
            if len(problem.split(' ')) < 3:
                problem+=' issues'
        return problem.strip()

    def weekdata(self, days=7):
        d = date.today()
        dates = []
        for i in range(0,int(days)):
            thisdate = str(d - timedelta(days=i))
            dates.append(thisdate)
        return dates
