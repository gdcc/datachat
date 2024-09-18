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
        return doi
    else:
        print("DOI not found.")

def get_json(doi):
    if 'FAKEDNS' in os.environ:
        dns = fakedns(os.environ['FAKEDNS'])        
        url = dns['*']
        for doirule in dns:
            if doirule in doi:
                url = dns[doirule].replace('%%id%%', doi.replace(':','%3A'))
        #r = requests.get(url)
        #json_ld_data = r.json()
        json_ld_data = datacache(doi)
        fields_to_remove = ['@type', '@context', 'distribution', 'recordSet', 'ore:aggregates', 'schema:hasPart']
        # Remove the specified fields
        for field in fields_to_remove:
            json_ld_data.pop(field, None)
        if 'ore:describes' in json_ld_data:
            json_ld_data['ore:describes'].pop(field, None) 
        return json_ld_data
    return

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

def fakedns(file_path):
    rules = {}
    try:
        with open(file_path, 'r') as file:
            # Read file line by line
            for line in file:
                # Strip any leading/trailing whitespaces/newlines
                line = line.strip()

                # Split the line by the delimiter ";"
                identifier, url_template = line.split(';')
                rules[identifier] = url_template
        return rules
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

def datacache(doi):
    url = ''
    if 'FAKEDNS' in os.environ: 
        dns = fakedns(os.environ['FAKEDNS'])
        url = dns['*']
        for doirule in dns:
            if doirule in doi:
                url = dns[doirule].replace('%%id%%', doi.replace(':','%3A'))

    cache_file = "%s/%s.json" % (os.environ['DATADIR'], doi.replace('/','_'))
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            content = json.load(file)
            return content
    else:
        r = requests.get(url)
        jsonld = r.json()
        with open(cache_file, 'w') as file:
            json.dump(jsonld, file, indent=4)
            return jsonld
    return
