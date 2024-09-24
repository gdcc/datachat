import requests
import re
import requests
import json
#from pyDataverse.api import DataAccessApi, SearchApi
#from pyDataverse.api import NativeApi
from elasticsearch import Elasticsearch
#from Levenshtein import distance
import geocoder
import arrow
import datetime, calendar
import os
import pandas as pd
from pymongo import MongoClient
TLIM = 0.1
PLIM = 0.5

class NowMuseum():
    def __init__(self, config=None, debug=False):
        self.config = config
        self.timeout = 120
        self.countryinfo = {}
        self.langfilter = {}
        self.alloweddomains = {}
        self.countries = []
        self.es = None
        self.queries = {}
        self.url = None
        self.DEBUG = None
        self.lexicon = []
        self.tonewords = []
        self.nolimits = False
        
    def nolimit(self, status):
        self.nolimits = status
        return
        
    def db_connect(self):
        connection = psycopg2.connect(user=os.environ['SOC_SUPERSETDB_USER'],password=os.environ['SOC_SUPERSETDB_PASSWORD'],host=os.environ['SOC_SUPERSETDB_HOST'],port=os.environ['SOC_SUPERSETDB_PORT'],database=os.environ['SOC_SUPERSETDB_DB'])

        cur = connection.cursor()
        connection.autocommit = True
        return cur

    def es_connect(self):
        self.es = Elasticsearch([self.config['elastichost']], http_auth=(self.config['elasticlogin'], self.config['elasticpassword']), port=self.config['elasticport'], timeout=self.timeout)
        return self.es

    def english_sentiments(self, phrase, localword=None, nosupervision=False):
        scores = {}
        finalscore = 0
        terms = []
        # [{'i': 148, 'p': ' ', 'res': {'neg': 0.175, 'neu': 0.825, 'pos': 0.0, 'compound': -0.5267}, 'language': 'en', 'keyword': 'restrictions'}]
        res = []
        try:
            soup = BeautifulSoup(phrase, 'html.parser')
            res = re.findall(r"[^.!?\n]+", soup.text)
        except:
            res = []
        
        SIA = SentimentIntensityAnalyzer()
        sentiments = []
        senwords = []
        #print("DEBUG %s" % res)
        for i in range(0, len(res)):
            active = False
            if not localword:
                active = True
            else:
                if len(localword):
                    for thisword in localword:
                        if thisword in res[i]:
                            active = True
                else:
                    if localword in res[i]:
                        active = True
            
            if active:
                p = res[i]
                score = SIA.polarity_scores(p)
                vs = SIA.polarity_scores(p)
                
                if localword:
                    if nosupervision:
                        microdata = { 'i': i, 'p': p, 'res': vs['valence_dict'], 'language': 'en', 'keyword': vs['sentiments'], 'ext': True } 
                        if not senwords:
                            senwords = vs['sentiments']
                        else:
                            for newitem in vs['sentiments']:
                                if newitem not in senwords:
                                    senwords.append(newitem)

                        for newitem in vs['sentiments']:
                            term = newitem['keyword']
                            if term not in terms:
                                terms.append(term)
                    else:
                        microdata = { 'i': i, 'p': p, 'res': vs['valence_dict'], 'language': 'en', 'keyword': localword } 
                else:
                    if 'sentiments' in vs:
                        microdata = { 'i': i, 'p': p, 'res': vs['valence_dict'], 'language': 'en', 'keyword': vs['sentiments'], 'ext': True } 
                        senwords = vs['sentiments']
                    else:
                        microdata = { 'i': i, 'p': p, 'res': vs['valence_dict'], 'language': 'en'}
                #print(type(vs))
                #print(vs)
                if vs['valence_dict']['neg'] >= TLIM:
                    finalscore = -1.25
                if vs['valence_dict']['pos'] >= PLIM:
                    finalscore = 1.25
                sentiments.append(microdata)
#        return (finalscore, sentiments, senwords)
        scores['result'] = sentiments
        if finalscore != 0:
            scores['score'] = finalscore
            scores['valence_dict'] = vs['valence_dict']
        if senwords:
            scores['senwords'] = senwords
        if terms:
            scores['terms'] = ', '.join(terms)
        return scores
    
    def french_sentiments(self, phrase, localword=None):
        finalscore = 0
        soup = BeautifulSoup(phrase, 'html.parser')
        res = re.findall(r"[^.!?\n]+", soup.text)
        SIA = fr.SentimentIntensityAnalyzer()
        sentiments = []
        
        for i in range(0, len(res)):
            active = False
            if not localword:
                active = True
            else:
                if localword in res[i]:
                    active = True
            
            if active:
                p = res[i]
                score = SIA.polarity_scores(p)
                vs = SIA.polarity_scores(p)
                microdata = { 'i': i, 'p': p, 'res': vs, 'language': 'fr', 'keyword': localword } 
                #print(type(vs))
                #print(vs)
                if vs['valence']['neg'] >= TLIM:
                    finalscore = -1.25
                sentiments.append(microdata)
        return (finalscore, sentiments)
    
    def connectmongo(self):
        client = MongoClient(os.environ['MONGO_HOST'], int(os.environ['MONGO_PORT']))
        db = client[os.environ['MONGO_DB']]
        collections = {}
        collections['col'] = db[os.environ['MONGO_COLLECTION']]
        return collections

    def read_excluded_ids(self, exclfile = "/data/excluded_ids.txt"):
        self.excldata = []
        with open(exclfile, "r+") as file1:
            rawdata = file1.read().split('\n')
            for i in range(1, len(rawdata)):
                if rawdata[i]:
                    self.excldata.append(rawdata[i])
        return self.excldata

    def drop_false_negative(self, exl):
        c = self.connectmongo(config)
        q = {"elastic_id" : { "$in": exl } }
        cursor = c['col'].find(q)
        for document in cursor:
            delid = document['elastic_id']
            print("Deleted %s" % delid)
            delquery = {"elastic_id" : { "$in": [delid] } }
            c['col'].delete_one(delquery)
        return True

    def get_all_countries(self, ctrfile=None):
        content = ''
        self.allcountries = {}
        self.code2country = {}
        if ctrfile:
            countries = []
            if not os.path.exists(ctrfile):
                ctrfile = "/app/datasets/countries.txt"

            with open(ctrfile, 'r') as reader:
                content = reader.read()

            for countryitem in content.split('\n'):
                try:
                    (country, code) = countryitem.split(',')
                    self.allcountries[country.lower()] = code.lower()
                    self.code2country[code.lower()] = country
                except:
                    skip = True
            return self.allcountries

    def countrysearch(self, q):
       codes = []
       for country in self.allcountries:
          try:
              if country.lower() in q.lower():
                  codes.append(self.allcountries[country])
          except:
              continue
       return codes

    def get_countrycodes(self, countryquery, country, alias):
        domainname = ''
        subquery = ''
        matches = re.findall(r'domain:([^ )]+)', countryquery)
        for item in matches:
            if '*' in item:
                domainname = item
        matches = re.findall(r'country:([^ )]+)', countryquery)
        for item in matches:
            if '*' in item:
                domainname = item
        if domainname:
            if ' ' in country:
                subquery = "country:%s OR domain:%s OR \"%s\"" % (domainname, domainname, country)
            else:
                subquery = "country:%s OR domain:%s OR %s" % (domainname, domainname, country)

        if country in alias:
            subqueries = alias[country].split(',')
            for countryalt in subqueries:
                if ' ' in countryalt:
                    subquery = subquery + " OR \"%s\"" % countryalt
                else:
                    subquery = subquery + " OR %s*" % countryalt
        return subquery

    def get_countries(self, ctrfile=None):
        if ctrfile:
            self.ctrfile = ctrfile
        else:
            ctrfile = "/tmp/countries.txt"
        self.countries = []
        content = ''
        with open(ctrfile, 'r') as reader:
            content = reader.read()

        for countryitem in content.split('\n'):
            try:
                (domains, languages, code, country) = countryitem.split('|')
                #print("%s %s" % (country, code))
                self.countries.append(country)
                self.countryinfo[code] = country
                self.langfilter[country] = languages.split(',')
                self.alloweddomains[country] = domains.split(',')
                #print(alloweddomains[country])
            except:
                skip = True
        return self.countries

    def get_keywords(self, url=None):
        terms = []
        
        if url:
            self.url = url
        r = requests.get(self.url)
        
        for keyword in r.json()['users_keywords']:
            if keyword:
                terms.append(keyword)
            
        for keyword in terms:
            for code in self.countryinfo:
                code1 = code
                code1 = code1.replace('country:', 'country:*')
                if code1 in str(keyword['keywords']):
                    query = keyword['keywords']
                    query = query.replace('&', ' ')
                    query = query.replace('country:', 'domain:')
                    # domain:*ke
                    c = re.search('domain\:\*(\w+)', query)
                    if c:
                        newcode = c.group(1)
                        #print(newcode)
                        query=re.sub('domain\:\*\w+', "(domain:*%s OR domain:twitter.com OR smitype:4)" % newcode, query)
                    if self.DEBUG:
                        print(query)
                    query = " ".join(query.split())
                    query = query.lstrip()
                    self.queries[self.countryinfo[code]] = query.strip() # " ".join(query.split()) #str(query.strip(' '))
        return self.queries

    def get_all_keywords(self, query):
        terms = []
        for term in re.split(r'(OR|and|\||\(|\))', query):
            checker = re.search(r'(OR|domain|and|country|smitype|language)', term) #.split(' and ')
            if not checker:
                if len(term) > 1:
                    term = term.replace('  ','')
                    term = term.replace('"','')
                    term = term.replace(' & ','')
                    if term:
                        terms.append(term)
        #print("!!! terms %s" % terms)
        return terms

    def set_el_string(self, query: str) -> str:
        return "(%s)" % query.replace("|", " OR ")\
            .replace("/", "")\
            .replace("&", " AND ")

    def count_news(self, keyword: dict,
             elastic: Elasticsearch,
             index: str,
             collection: str,
             start=int(arrow.utcnow().shift(hours=-198).timestamp()),
             end=int(arrow.utcnow().timestamp())):
        size = 10000
        data = []
        if self.nolimits:
            query = set_el_string(keyword['keywords'])
        else:
            query = set_el_string(keyword['keywords']) + " AND timestamp:[{} TO {}]".format(start, end)
        
        if elastic.indices.exists(index=index):
            res = elastic.count(index, collection,
                             body={
                                 "query": {
                                    "query_string": {
                                        "query": query,
                                        "default_operator": "AND"
                                        }
                                 },
                             }
                             )
        return res["count"]
    
    def get_news(self, keyword: dict,
             elastic: Elasticsearch,
             index: str,
             collection: str,
             start=int(arrow.utcnow().shift(hours=int(-24)).timestamp()),
             end=int(arrow.utcnow().timestamp())):
        size = 10000
        data = []
        if keyword['keywords']:
            query = keyword['keywords'] # self.set_el_string(keyword['keywords'])
        else:
            query = self.set_el_string(keyword['keywords']) + " AND timestamp:[{} TO {}]".format(start, end)
        #query = self.set_el_string(keyword['keywords'])
        print(query)
        if elastic.indices.exists(index=index):
            res = elastic.search(index, collection,
                             body={
                                 "query": {
                                    "query_string": {
                                        "query": query,
                                        "default_operator": "AND"
                                        }
                                 },
                                 "size": size
                             },
                             scroll="1m"
                             )

            while res['hits']['hits']:
                try:
                    sid = res['_scroll_id']
                    # get batch with data
                    scroll_res = res['hits']['hits']
                    data.extend(scroll_res)
                    # get next batch
                    res = elastic.scroll(scroll_id=sid, scroll="1m")

                except KeyError:
                    break
        else:
            return []
        return data
    
    def get_news_count(self, keyword: dict,
             elastic: Elasticsearch,
             index: str,
             collection: str,
             start=int(arrow.utcnow().shift(hours=int(-24)).timestamp()),
             end=int(arrow.utcnow().timestamp())):
        size = 10000
        data = []
        if keyword['keywords']:
            query = keyword['keywords'] # self.set_el_string(keyword['keywords'])
        else:
            query = self.set_el_string(keyword['keywords']) + " AND timestamp:[{} TO {}]".format(start, end)
        #query = self.set_el_string(keyword['keywords'])
        print(query)
        if elastic.indices.exists(index=index):
            res = elastic.count(index, collection,
                             body={
                                 "query": {
                                    "query_string": {
                                        "query": query,
                                        "default_operator": "AND"
                                        }
                                 },
                             },
                             )
            return res['count']
        return 

    def load_custom_lexicon(self, lexiconfile):
        df = pd.read_csv (lexiconfile, sep='\t')
        for i in df.index:
            #for word in df.iloc[[i]]['English']:
            #    print(word)
        #    print(df.iloc[[i]]['Українська'].values[0])
        #    print(df.iloc[[i]]['English'].values[0])
            self.lexicon.append({'id': i, 'ua': df.iloc[[i]]['Українська'].values[0], 'en': df.iloc[[i]]['English'].values[0], 'fr': df.iloc[[i]]['French'].values[0], 'pt': df.iloc[[i]]['Portuguese'].values[0], 'es': df.iloc[[i]]['Spanish'].values[0]})
        return self.lexicon
    
    def load_custom_sentiments(self, sentimentfile):
        with open(sentimentfile, 'r') as reader:
            words = reader.read()
        sent = ""
        
        if words:
            for word in words.split('\n'):
                if len(word) > 1:
                    if sent:
                        sent = sent + " | \"%s\" " % word
                        self.tonewords.append(word)
                    else:
                        sent = word
                        self.tonewords = [ word ]
        return sent
    
    def get_domains(self, news):
        known = {}
        for i in news:
            domain = i['_source']['domain']
            if not domain in known:
                #ids = ids + ", " + i['_source']['domain']
                known[domain] = 1
            else:
                known[domain] = known[domain] + 1
        return known
    
    def get_alerts(self, label, newsid=None):
        c = self.connectmongo()
        if not newsid:
#            q = {label: True}
            startdate = datetime.datetime(2023, 8, 5, 0, 0, 0)
            q = {label: True, 'datetime': {"$gt": startdate}}
        else:
            q = {label: True, 'elastic_id': newsid }
                 
        print(q)
        cursor = c['col'].find(q)
        known = {}
        data = {}
        alerts = []
        if q:
            for document in cursor:
                data = {}
                data['id'] = document['elastic_id']
                data['url'] = document['url']
                data['result'] = document['result']
                data['words'] = document['sentimental_words']
                alerts.append(data)
        return alerts

    def get_sentiments(self, idlist):
        c = self.connectmongo()
        q = {"elastic_id" : { "$in": idlist } }
        cursor = c['col'].find(q)
        known = {}
        NEGRATE = -1 #-0.5
        POSRATE = 1 #1.3
        DEBUG = False
        sentiwords = {}
        sentidata = {}
        newsids = []
        for document in cursor:
            data = {}
            data['id'] = document['elastic_id']
            data['url'] = document['url']
            if not data['url'] in known:
                #print(document['url'])
                neg = {}
                kword = { 'odds': 1, 'no': 2, 'odd': 3, 'arsenal': 4 }
                negkeywords = []
                poskeywords = []
                for worditem in document['sentimental_words']['sentiments']:
                    #worditem['rank'] = worditem['rate']
                    if float(worditem['rank']) < NEGRATE:
                        if not worditem['keyword'].lower() in kword:
                            if DEBUG:
                                print(worditem)
                            kword[worditem['keyword']] = worditem['rank']
                            negkeywords.append(worditem['keyword'])
                    if float(worditem['rank']) > POSRATE:
                        if not worditem['keyword'].lower() in kword:
                            if DEBUG:
                                print(worditem)
                            kword[worditem['keyword']] = worditem['rank']
                            poskeywords.append(worditem['keyword'])
            #print(document['sentimental_words'])
                sentiwords[data['id']] = {'negative': ', '.join(negkeywords), 'positive': ', '.join(poskeywords) }
                newsids.append(data['id'])
            known[data['url']] = 1
        sentidata['words'] = sentiwords
        print("WORDS %s" % sentiwords)
        sentidata['newsids'] = newsids
        return sentidata

    def create_sentiment(self, newsitem, sentdata):
        data = {}
        thistype = "new"
        if 'urlid' in newsitem:
            data["elastic_id"] = str(newsitem['urlid'])
            data['news_id'] = str(newsitem['urlid'])
        if 'id' in newsitem:
            data["elastic_id"] = str(newsitem['id'])
            data['news_id'] = str(newsitem['id'])

        data["kw_body"] = sentdata['q']
        data["result"] = sentdata['result']
        if 'language' in newsitem:
            data['language'] = newsitem['language']
        else:
            data['language'] = 'en'
            
        iperlist = sentdata['iperlist']
        iorglist = sentdata['iorglist']
        sentimental_wordslist = sentdata['sentwords']
        data['total_rating'] = sentdata['total_rating']
        data['indexname'] = 'index'
        data['doc_type'] = "2"
        data['type'] = 'new'
        if newsitem['smitype'] == 7:
            data['smitype'] = "SocialMedia"
        else:
            data['smitype'] = "News"
        data['timestamp'] = newsitem['timestamp']
        data['foundtime'] = newsitem['foundtime']
        data['datetime'] = datetime.datetime.fromtimestamp(data['timestamp']) #, None) #datetime.datetime.strptime(thisdate, "%Y-%m-%dT%H:%M:%S")
        data['url'] = newsitem['url']
        data['domain'] = newsitem['domain']
        item = {"type": thistype, "result": data['result'], "language": data['language'], "elastic_id" : data['elastic_id'], "news_id" : data['news_id'], "kw_body" : data['kw_body'], "geo" : [ ], "i_loc" : [ ], "i_per" : iperlist, "i_org" : iorglist, "sentimental_words" : sentimental_wordslist, "total_rating" : data['total_rating'], "domain_stats" : { "website_audience" : {  }, "geography" : {  } }, "index" : data['indexname'], "smi_type" : data['smitype'], "doc_type" : data['doc_type'], "timestamp" : data['timestamp'], "foundtime" : data['foundtime'], "datetime" : data['datetime'], "url" : data['url'], "domain" : data['domain'] }
        content = ""
        if 'title' in newsitem:
            content = newsitem['title']
        if 'text' in newsitem:
            content = content + ' ' + newsitem['text']
        c = self.connectmongo()
        print(item)
        c['col'].insert_one(item)
        return item

    def mediasentiments(self, countries, queries, mainkeyword=None):
        cache = {}
        lexicon = self.load_custom_lexicon(os.environ['NEGATIVEVOCABULARY']) #"/tmp/NegativeWords.tsv")
        self.get_countries(os.environ['COUNTRYFILE'])
        brands = self.brands_to_array(self.get_keywords(os.environ['KEYWORDSURL']))

        for country in self.get_keywords(os.environ['KEYWORDSURL']):
            print(country)
            try:
                q = queries[country]
            except:
                print("Country %s not found" % country)
                continue
            mainq = q
            sentimentfile = os.environ['SCAMVOCABULARY'] #"/tmp/scam.txt"
            countries = []
            sent = self.load_custom_sentiments(sentimentfile)

            #for itemlex in lexicon:
            if mainq:
                #for lang in ['en','fr','pt','es']:
                if sent:
                    #sent = "\"%s\"" % itemlex[lang]
                    keywords= {}
                    DEBUG = False
                    today = datetime.date.today()
                    yesterday = today - datetime.timedelta(days=1)
                    tomorrow = today + datetime.timedelta(days=1)

                    if not mainkeyword:
                        sentiment_query = "(%s) AND fixdate:(\"%s\" | \"%s\")" % (q, today, yesterday)
                    else:
                        q = re.sub('^\(.+?\)', 'something', q)
                        sentiment_query = "(%s) AND fixdate:(\"%s\" | \"%s\" | \"%s\")" % (q, today, yesterday, tomorrow)
                    mainq = q
                    keywords['keywords'] = sentiment_query
                    print(keywords['keywords'])
                    ELASTIC = {'index': 'streamfr', 'collection': 'streamfr' }
                    go = False
                    if not sentiment_query in cache:
                        go = True

                    if go:
                        cache[sentiment_query] = True
                        news = self.get_news(keyword=keywords,
                            elastic=self.es,
                            index=ELASTIC['index'],
                            collection=ELASTIC["collection"])

                        # Collecting known news articles
                        newsids = []
                        if len(news):
                            print("%s %s" % (len(news), sentiment_query))
                        for item in news:
                            newsids.append(item['_id'])

                        knownids = self.get_sentiments(newsids)['newsids']

                        for item in news:
                            if not item['_id'] in knownids:
                                enabled = True
                                if enabled:
                                    sentdata = {}
                                    sentdata['q']= mainq
                                    per = []
                                    #per = [{ "word" : itemlex['ua'], "count" : 1 }]
                                    
                                    #senwords = [ { "keyword" : itemlex['ua'], "rate" : -1.25 } ]
                                    sentdata['iperlist'] = per
                                    sentdata['iorglist'] = []
                                    sentdata['country'] = country
                                    #sentdata['sentwords'] = senwords
                                    sentdata['total_rating'] = 1.9

                                    alltexts = ''
                                    if 'title' in item['_source']:
                                        try:
                                            alltexts = alltexts + item['_source']['title']
                                        except:
                                            continue
                                    if 'text' in item['_source']:
                                        alltexts = alltexts + item['_source']['text']

                                    result = []
                                    score = 0
                                    try:
                                        result = self.custom_sentiment_analysis(int(os.environ['DISTANCELIMIT']), brands, item, lexicon)
                                    except:
                                        print("ERROR with %s" % item['_id'])

                                    checker = re.search('something', alltexts)
                                    if checker:
                                        score = 2

                                    if result:
                                        sentdata['result'] = result
                                        if 'language' in item['_source']:
                                            sentdata['language'] = item['_source']['language'] 
                                        #senwords = [ { "keyword" : itemlex['ua'], "rate" : score } ]
                                        sentdata['sentwords'] = self.report_sentiments(result)
                                        self.create_sentiment(item['_source'], sentdata)
                            #domains = mq.get_domains(news)
                            #print(domains)
                            else:
                                print("Ready %s" % item['_id'])
        return True

    def distance_brand_sentiments(self, text, brandwords, sentwords=None):
        word_list = text.lower().split()
        brands = {}
        sent = {}
        for R in range(0,len(word_list)):
            if word_list[R] in brandwords:
                for word0 in brandwords:
                    if word_list[R] == word0.lower():
                        if word0 not in brands:
                             brands[word0] = [ R ]
                        else:
                             brands[word0].append(R)
                    
            if sentwords:
                if word_list[R] in sentwords:
                    for word1 in sentwords:
                        if word1 in word_list[R]:
                            sent[word1] = R   
        if brands:
            r = { 'brands': brands, 'sentiments': sent, 'text': text }
            return r
        return

    def custom_sentiment_analysis(self, LIMIT, brands, item, lexicon):
        sentwords = []
        ratings = {}
        alltexts = ''
        if not 'language' in item['_source']:
            item['_source']['language'] = 'en'
        if 'title' in item['_source']:
            try:
                alltexts = str(item['_source']['title'])
            except:
                alltexts = ''

        if 'text' in item['_source']:
            alltexts = alltexts + ". " + item['_source']['text']            
        alltexts = alltexts.replace('#', ' ').replace(',', ' ').replace('!', ' ').replace('\n', '. ')
        #for itemlex in lexicon:
        for lang in ['en', 'fr','pt','es']: 
            if lang:
                r = { 'result':  '' }
                if 'language' in item['_source']:
                    try:
                        if item['_source']['language'] == 'fr':
                            r = self.french_sentiments(alltexts)
                                
                        if item['_source']['language'] == 'en':
                            r = self.english_sentiments(alltexts)
                    except:
                        continue
                                
                #print("DEBUG %s" % str(r))
                for line in r['result']:
                    if 'keyword' in line:
                        k = line['keyword']#['keyword']
                        for localitem in k:
                            ratings[localitem['keyword'].lower()] = localitem #r['result'][0]['keyword']
                            if not localitem['keyword'].lower() in sentwords: 
                            #print(r['result'][0]['keyword'])
                                sentwords.append(localitem['keyword'].lower())
    
        alias = {}
        print(sentwords)
        for itemlex in lexicon:
            for lang in ['en', 'fr','pt','es']: 
                for keyword in sentwords:
                    #print("%s -> %s (%s)" % (itemlex[lang], itemlex['ua'], alias))
                    try:
                        if len(keyword) > 3 and keyword in itemlex[lang]:
                            if not keyword in alias:
                                alias[keyword] = itemlex['ua']
                    except:
                        continue
        res = self.distance_brand_sentiments(alltexts, brands, sentwords)
        #print(res)
        relationships = {}
        if res:
            d = {'result': res, 'rating': ratings}
            
            MIN = 1000
            for brand in d['result']['brands']:
                brandpositions = d['result']['brands'][brand]
                for spos in brandpositions:
                    pos = int(spos)
                    #print("POS %s" % pos)
                    for s in d['result']['sentiments']:
                        if abs(int(d['result']['sentiments'][s]) - pos) < MIN:
                            worddistance = abs(int(d['result']['sentiments'][s]) - pos)
                            #print(info['result']['sentiments'][s])
                            if worddistance < LIMIT:
                                print(d['result'])
                                try:
                                    test = alias[s]
                                except:
                                    alias[s] = ''
                                
                                if brand in relationships:
                                    thisrank = { 'distance': int(worddistance), 'keyword': s, 'rank': d['rating'][s]['rate'] }
                                    if len(alias[s]) > 0:
                                        thisrank['alias'] = alias[s] 
                                    relationships[brand].append(thisrank)
                                else:
                                    thisrank = { 'distance': int(worddistance), 'keyword': s, 'rank': d['rating'][s]['rate'] }
                                    if len(alias[s]) > 0:
                                        thisrank['alias'] = alias[s]
                                    relationships[brand] = [thisrank]
            return relationships
        return

    def deep_sentiment_analysis(self, LIMIT, brands, alltexts, lexicon):
        sentwords = []
        ratings = {}
        relationships = {}
        alltexts = alltexts.replace('#', ' ').replace(',', ' ').replace('!', ' ')
        for itemlex in lexicon:
            for lang in ['en', 'fr','pt','es']: 
                if lang == 'en':
                    #print(itemlex[lang])
                    sent = "\"%s\"" % itemlex[lang]
            r = self.english_sentiments(alltexts) #, itemlex['en'])
            print("TEST")
            print(r)
            if 'keyword' in r['result'][0]:
                k = r['result'][0]['keyword']#['keyword']
                for item in k:
                    ratings[item['keyword'].lower()] = item #r['result'][0]['keyword']
                    if not item['keyword'].lower() in sentwords: 
                    #print(r['result'][0]['keyword'])
                        sentwords.append(item['keyword'].lower())
    
        res = self.distance_brand_sentiments(alltexts, brands, sentwords)
        if res:
            d = {'result': res, 'rating': ratings}
            MIN = 1000
            for brand in d['result']['brands']:
                pos = int(d['result']['brands'][brand])
                for s in d['result']['sentiments']:
                    if abs(int(d['result']['sentiments'][s]) - pos) < MIN:
                        worddistance = abs(int(d['result']['sentiments'][s]) - pos)
                        #print(info['result']['sentiments'][s])
                        if worddistance < LIMIT:
                            print(d['result'])
                            if brand in relationships:
                                thisrank = { 'distance': int(worddistance), 'keyword': s, 'rank': d['rating'][s]['rate'] }
                                relationships[brand].append(thisrank)
                            else:
                                relationships[brand] = [{ 'distance': int(worddistance), 'keyword': s, 'rank': d['rating'][s]['rate'] }]
            return relationships
        return

    def brands_to_array(self, keywords):
        allkeywords = []
        for country in keywords:
            k = self.get_all_keywords(keywords[country])
            for thiskeyword in k:
                if not thiskeyword.strip() in allkeywords:
                    allkeywords.append(thiskeyword.strip())
        return allkeywords

    def array_to_brands(self, keywords):
        allkeywords = []
        if keywords:
            k = self.get_all_keywords(keywords)
            for thiskeyword in k:
                if not thiskeyword.strip() in allkeywords:
                    allkeywords.append(thiskeyword.strip())
        return allkeywords

    def report_sentiments(self, info):
        sentidata = []
        notes = ''
        for brand in info:
            for keywordline in info[brand]:
                keywordline['brand'] = brand
                if brand in notes:
                    thisnote = "%s: %s(%s)" % (brand, keywordline['keyword'], keywordline['distance'])
                    notes = notes + ' ' + thisnote
                else:
                    thisnote = "%s: %s(%s)" % (brand, keywordline['keyword'], keywordline['distance'])
                    notes = thisnote 
                    
                if 'alias' in keywordline:
                    keepkeyword = keywordline['keyword']
                    keywordline['keyword'] = keywordline['alias']
                    keywordline['alias'] = keepkeyword
                sentidata.append(keywordline)
        return { 'sentiments': sentidata, 'notes': notes }

    def get_levenstein_position(text, inputs):
        words = text.split()
        d = {}
        for w in inputs:
            distances = [distance(w, word) for word in words]
            #closest = words[distances.index(min(distances))]
            d[w] = distances.index(min(distances))
        return d
