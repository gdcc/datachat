import requests
import re
import os
import json

def get_doi_from_text(text):
    # Regular expression pattern to capture DOI
    doi_pattern = r'(doi\:\S+)'

    # Find DOI in the string
    match = re.search(doi_pattern, text)

    if match:
        doi = match.group(1)  # Extracted DOI
        #print("Extracted DOI:", doi)
        return doi
    else:
        print("DOI not found.")

def get_json(doi):
    url = "https://dataverse.harvard.edu/api/datasets/export?exporter=OAI_ORE&persistentId=%s" % doi.replace(':','%3A')
    url = "https://dataverse.harvard.edu/api/datasets/export?exporter=croissant&persistentId=%s" % doi.replace(':','%3A')
    if 'dans' in doi:
        url = "https://portal.devstack.odissei.nl/api/datasets/export?exporter=croissant&persistentId=%s" % doi.replace(':','%3A')
    if '10.5072' in doi:
        url = "https://database.sharemusic.se/api/datasets/export?exporter=croissant&persistentId=%s" %  doi.replace(':','%3A')
    r = requests.get(url)
    json_ld_data = r.json()
    fields_to_remove = ['@type', '@context', 'distribution', 'recordSet', 'ore:aggregates', 'schema:hasPart']

    # Remove the specified fields
    for field in fields_to_remove:
        json_ld_data.pop(field, None)
    if 'ore:describes' in json_ld_data:
        json_ld_data['ore:describes'].pop(field, None) 
    return json_ld_data

def query_ollama(prompt):
    s = requests.Session()
    output=''
    with s.post("%s/api/generate" % os.environ['OLLAMA'], json={'model': os.environ['MODEL'], 'prompt': prompt}, stream=True) as r:
        for line in r.iter_lines():
            if line:
                j = json.loads(line)
                if "response" in j:
                    output = output +j["response"]
    return output


def form_prompt(doi):
    json_ld_data = get_json(doi)
    description_cr = f"""Consider the following JSON-LD data about a creator of a dataset:
{json.dumps(json_ld_data, indent=2)}

The "name" field describes a title.
The "description" field describes a description.
The "keywords" field describes a list of keywords.
The "datePublished" field describes date when dataset was created"
The "creator" field describes a person, where:
- "givenName" is the creator's first name.
- "familyName" is the creator's last name.
- "name" provides the full name in "familyName, givenName" format.
"""

    return description_cr
