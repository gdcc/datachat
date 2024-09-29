import json
from elasticsearch import Elasticsearch
from .AI import AIMaker 
import app
import arrow
import os
import re
import textwrap
from datetime import datetime, date, timedelta
import pytz
import textwrap
from calendar import timegm
from textblob import TextBlob
from .config import entities
import langid
import requests, json, io, sys
import random
from collections import Counter
from nltk.util import ngrams
import nltk
from time import sleep
import spacy
nlp = spacy.load('en_core_web_sm')
nltk.download('punkt_tab')

class Attention():
    def __init__(self, question=None, config=None, LLAMA_URL=None, debug=False):
        self.keywords = []
        self.maintopic = []
        self.CYCLES = 2
        if LLAMA_URL:
            self.llama_url = LLAMA_URL
        else:
            self.llama_url = os.environ['OLLAMA']
        if question:
            self.question = question
            self.answer()
        else:
            self.question = None

    def get_topics(self):
        return set(self.maintopic)
        
    def extract_from_quotes(self, text):
        # Use a regular expression to extract the content within double quotes
        matches = re.findall(r'"(.*?)"', text)
        if matches:
            return matches[0]
        else:
            return text

    # Function to extract repeated sequences (ngrams)
    def find_repeated_sequences(self, data, n=2):
        # Initialize a list to store all tokens
        all_ngrams = []
        
        # Iterate through each string in the list
        for entry in data:
            # Remove numbers and quotes
            clean_entry = re.sub(r'^\d+,:"', '', entry).strip('"')
            
            # Tokenize the text (split into words)
            words = nltk.word_tokenize(clean_entry.lower()) # convert to lowercase for uniformity
            
            # Generate n-grams (combinations of 'n' words)
            n_grams = ngrams(words, n)
            
            # Add the n-grams to the all_ngrams list
            all_ngrams.extend(n_grams)
        
        # Count the frequency of each n-gram
        ngram_counts = Counter(all_ngrams)
        
        # Find repeated n-grams (occurring more than once)
        repeated_ngrams = {' '.join(ngram): count for ngram, count in ngram_counts.items() if count > 1}
        
        return repeated_ngrams
        
    def changequestion(self, question):
        self.keywords = []
        self.question = question
        self.answer()
        return
        
    def extract_queries(self, data_string):
        # Split the string by line breaks and remove empty lines
        lines = [line.strip() for line in data_string.splitlines() if line.strip()]
        
        # Initialize an empty list to store the queries
        queries = []
        self.maintopic = []
        # Loop through each line and extract the part after the colon
        for line in lines:
            # Find the query by splitting on the colon and stripping the quotes
            queryblock = line.split("CSV#")#[1].strip().strip('"')
            for query in queryblock:
                if 'NewKey' in query:
                    queries.append(self.extract_from_quotes(query.replace('NewKey','')))
                if 'MainKey' in query:
                    queries.append(self.extract_from_quotes(query.replace('MainKey','')))
                    self.maintopic.append(self.extract_from_quotes(query.replace('MainKey','')))
        
        return queries
    
    def answer(self):
        config = {}
        ai = AIMaker(config, LLAMA_URL=self.llama_url)
        ai.changefocus("the meaning")
        ai.changerole("data expert")
        newprompt = f"You are %%role%%. Your task is to apply %%focus%% for message %%message%% and give back \"primary keyword\" or \"head term\", for example in phrase \"coffee\" production term \"coffee\" is head term. Put head terms in new line after CSV#MainKey, for example, CSV#MainKey1 \"coffee\". Also give exact match keywords (\"compound terms\"). Give them back in every new line after CSV#NewKey1, for example, CSV#NewKey1 \"climate change\", CSV#NewKey2 \"temperature change\". Produce two groups of answer: including 2 and 3 terms."
        ai.changeprompt(newprompt)
        for i in range(0,self.CYCLES):
            anno = ai.llama3(self.question)
            self.keywords+=(self.extract_queries(anno))
        return self.keywords

    def analyze_question(self, qa, debug=False):
        doc = nlp(qa)
        entities = {}
        # Identifying action (verb) in the question
        action = None
        for token in doc:
            if token.pos_ == 'VERB' and token.dep_ == 'ROOT':
                action = token.text
                break
    
        # Identifying direct objects and main subjects
        subjects = []
        objects = []
        for token in doc:
            if token.dep_ == 'nsubj' or token.dep_ == 'nsubjpass':  # Subject
                subjects.append(token.text)
            elif token.dep_ == 'dobj' or token.dep_ == 'attr':  # Direct Object
                objects.append(token.text)
    
        # Identifying named entities (like people, organizations, etc.)
        named_entities = []
        for ent in doc.ents:
            named_entities.append((ent.text, ent.label_))
    
        # Prepositions and relationships
        relationships = []
        for token in doc:
            if token.pos_ == 'ADP':  # Prepositions (like 'by', 'with', etc.)
                phrase = ' '.join([tok.text for tok in token.subtree])
                relationships.append(phrase)
    
        # Noun Phrases
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        if action:
            entities['action'] = action
        if subjects:
            entities['subjects'] = subjects
        if objects:
            entities['objects'] = objects
        if named_entities:
            entities['named_entities'] = named_entities
        if relationships:
            entities['relationships'] = relationships
        if noun_phrases:
            entities['noun_phrases'] = noun_phrases
        if debug:
            # Printing out the analysis
            print(f"Action Verb: {action}")
            print(f"Subjects: {subjects}")
            print(f"Objects: {objects}")
            print(f"Named Entities: {named_entities}")
            print(f"Relationships: {relationships}")
            print(f"Noun Phrases: {noun_phrases}")
        return entities

