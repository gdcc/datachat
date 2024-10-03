import requests
import re
import os
import json
from pyDataverse.Croissant import Croissant

def get_doi_from_text(text):
    # Regular expression pattern to capture DOI
    doi_pattern = r'^(\S+)\/dataset\S+(doi\:\S+)'

    # Find DOI in the string
    match = re.search(doi_pattern, text)

    if match:
        doi = match.group(1)  # Extracted DOI
        return (match.group(1), match.group(2))
        #return doi
    else:
        doi_pattern = r'https\:\/\/doi.org\/(\S+)'
        match = re.search(doi_pattern, text)
        if match:
            doi = "doi:%s" % match.group(1)
            return doi.replace('"','')
        print("DOI not found.")
        # check for handle
        #hdl:10622/SOS0KC#
        hdl_pattern = r'(hdl\:\S+)'
        match = re.search(hdl_pattern, text)
        if match:
            return (False, match.group(1))
    return (False, False)

def get_json(doi):
    if 'FAKEDNS' in os.environ:
        dns = fakedns(os.environ['FAKEDNS'])        
        url = dns['*']
        for doirule in dns:
            if doirule in doi:
                url = dns[doirule].replace('%%id%%', doi.replace(':','%3A'))
        json_ld_data = datacache(doi)
        fields_to_remove = ['@type', '@context', 'distribution', 'recordSet', 'ore:aggregates', 'schema:hasPart', 'dateCreated']
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

def datacache(doi, url=False):
    url = ''
    if 'FAKEDNS' in os.environ: 
        dns = fakedns(os.environ['FAKEDNS'])
        url = dns['*']
        for doirule in dns:
            if doirule in doi:
                url = dns[doirule].replace('%%id%%', doi.replace(':','%3A'))

    cache_file = "%s/%s.json" % (os.environ['IDATADIR'], doi.replace('/','_'))
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            content = json.load(file)
            return content
    else:
        jsonld = { "status":"ERROR" }
        try:
            r = requests.get(url)
            jsonld = r.json()
        except:
            skip = True

        try:
            if 'ERROR' in jsonld['status']:
                #host = "https://dataverse.nl"
                PID = doi #"doi:10.34894/YH"
                thishost = False
                if 'hostname' in os.environ:
                    thishost = os.environ['hostname']
                croissant = Croissant(PID, host=thishost) 
                jsonld = croissant.get_record()
        except:
            skip = True

        with open(cache_file, 'w') as file:
            json.dump(jsonld, file, indent=4, default=str)
            return jsonld
    return

def applyfilter(datasource):
    if 'FILTER' in os.environ:
        filters = os.environ['FILTER'].split(',')
        for filter in filters:
            if filter in str(datasource):
                return True 
        return False 
    else:
        return True

def sources():
    if 'SOURCES' in os.environ:
        if 'http' in os.environ['SOURCES']:
            data = requests.get(os.environ['SOURCES'])
            hosts = ['https://dataverse.harvard.edu'] 
            hosts = []
            for instance in data.json()['installations']:
                hostname = instance['hostname']
                if not 'http' in hostname:
                    hostname = "https://%s" % hostname
                if not hostname in hosts and applyfilter(instance):
                    hosts.append(hostname)
            hosts.append('https://portal.staging.odissei.nl')
            return hosts
        else: 
            sources = os.environ['SOURCES']
            return sources.replace('"','').replace('\n','').split(',')
    return 

def linked_data_query_constructor(textinput):
    json_pattern = re.search(r'({.*})', textinput, re.DOTALL)

    if json_pattern:
        json_string = json_pattern.group(1)

        json_string = json_string.replace("'", '"')
        #for lineitem in json_string.split('\n'):
        #    if lineitem[-1:] == ']':
        #        lineitem+=','
        try:
            extracted_query = json.loads(json_string)
            if 'keywords' in extracted_query:
                searchquery = ''
                for keyword in extracted_query['keywords']:
                    searchquery = "%s AND %s" % (searchquery, keyword)
            return extracted_query
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
    else:
        print("No JSON found in the text.")
    return
