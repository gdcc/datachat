from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json
from elasticsearch import Elasticsearch
from app.AI import AIMaker 
import app
import arrow
import re
import textwrap
from datetime import datetime, date, timedelta
import pandas as pd
from io import StringIO
config = {}
import requests

ai = AIMaker(config, LLAMA_URL="10.147.18.193:8093")
def extract_json_ld(text):
    # Define the regular expression to match the JSON-LD block
    # This will match everything between the code block delimiters: ```
    json_ld_match = re.search(r'```(.*?)```', text, re.DOTALL)
    
    if json_ld_match:
        # Extract the matched JSON-LD content
        json_ld_content = json_ld_match.group(1).strip()
        return json_ld_content

        try:
            # Load the JSON content as a Python dictionary
            json_ld_data = json.loads(json_ld_content)
            return json_ld_data
        except json.JSONDecodeError:
            print("Error: The extracted content is not valid JSON.")
            return None
    else:
        print("No JSON-LD content found in the input.")
        return None

# Create a FastAPI instance
app = FastAPI()

# Define a root route
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app!"}

# Define a route with a path parameter
@app.get("/url/")
def read_item(url: str = None):
    ai.changefocus("transformation")
    ai.changerole("ddi expert")
    newprompt = f"You are %%role%%. Use %%focus%% for message %%message%% and produce ddi-c codebook"
    ai.changeprompt(newprompt)
    filename = "predictiondata__2021-01-18.csv"
    
    exampleurl = "https://raw.githubusercontent.com/gdcc/datachat/refs/heads/ddi/config/example.csv"
    example = requests.get(exampleurl).text
    #testurl = "https://raw.githubusercontent.com/gdcc/datachat/refs/heads/ddi/config/test.csv"
    testurl = url
    #return testurl
    test = requests.get(testurl).text
    #return test
    ddiurl = "https://raw.githubusercontent.com/gdcc/datachat/refs/heads/ddi/config/example.ddi"
    ddiurl = "https://raw.githubusercontent.com/gdcc/datachat/refs/heads/ddi/config/example.cdi"
    ddiurl = "https://raw.githubusercontent.com/gdcc/datachat/refs/heads/ddi/config/example2.cdi"
    ddirecord = requests.get(ddiurl).text
    print(test)
    try:
        dfdata = pd.read_csv(StringIO(test), sep=',')
    except:
        dfdata = pd.read_csv(StringIO(test), sep='\t') 
    csv_string = dfdata.head()[0:10].to_csv(index=False, sep=',')
    num_rows = len(dfdata)
    
    qa = f"in CSV format {example} as example and learn how to produce record {ddirecord}. Create the same kind of record for data in CSV, use file {filename}, fill <caseQnty> with value of '{num_rows}' since there are {num_rows} records in the provided CSV data:\n {csv_string} "
    
    anno = ai.llama3(qa)
    ddi = re.findall(r'(<?xml\s+version.*?<\/codeBook>)', anno, re.DOTALL)
    print(anno)
    json_ld_string = extract_json_ld(anno)
    json_ld_data = json.loads(json_ld_string)
    return json_ld_data
    #return JSONResponse(content=json_ld_data, media_type="application/ld+json")


