from collections import Counter
from rdflib import Graph, URIRef, Literal, BNode, Namespace, RDF

class TripleSet():
    def __init__(self, dataitem, ingest=False, debug=False):
        self.alllabels = []
        self.nlp = []
        self.string_data = None
        self.url = None
        self.g = Graph()
        self.ns1 = Namespace("https://now.museum/")
        if debug:
            self.DEBUG = debug
        else:
            self.DEBUG = False

        self.spacyentities ={
  "PERSON": {
    "description": "People, including fictional characters",
    "relationship": "PERSON",
    "crosswalks": "authorName, authorAffiliation",
    "WikiData_URI": "http://www.wikidata.org/entity/Q5"
  },
  "NORP": {
    "description": "Nationalities or religious or political groups",
    "relationship": "NORP",
    "WikiData_URI": "http://www.wikidata.org/entity/Q7278"
  },
  "FAC": {
    "description": "Buildings, airports, highways, bridges, etc.",
    "relationship": "FAC",
    "WikiData_URI": "http://www.wikidata.org/entity/Q41176"
  },
  "ORG": {
    "description": "Companies, agencies, institutions, etc.",
    "relationship": "ORG",
    "crosswalks": "authorName, authorAffiliation",
    "WikiData_URI": "http://www.wikidata.org/entity/Q43229"
  },
  "GPE": {
    "description": "Countries, cities, states",
    "relationship": "GPE",
    "crosswalks": "locations",
    "WikiData_URI": "http://www.wikidata.org/entity/Q6256"
  },
  "LOC": {
    "description": "Non-GPE locations, mountain ranges, bodies of water",
    "relationship": "LOC",
    "crosswalks": "locations",
    "WikiData_URI": "http://www.wikidata.org/entity/Q82794"
  },
  "PRODUCT": {
    "description": "Objects, vehicles, foods, etc. (not services)",
    "relationship": "PRODUCT",
    "WikiData_URI": "http://www.wikidata.org/entity/Q2424752"
  },
  "EVENT": {
    "description": "Named hurricanes, battles, wars, sports events",
    "relationship": "EVENT",
    "WikiData_URI": "http://www.wikidata.org/entity/Q1656682"
  },
  "WORK_OF_ART": {
    "description": "Titles of books, songs, artworks, etc.",
    "relationship": "WORK_OF_ART",
    "WikiData_URI": "http://www.wikidata.org/entity/Q838948"
  },
  "LAW": {
    "description": "Named documents made into laws",
    "relationship": "LAW",
    "WikiData_URI": "http://www.wikidata.org/entity/Q7748"
  },
  "LANGUAGE": {
    "description": "Any named language",
    "relationship": "LANGUAGE",
    "WikiData_URI": "http://www.wikidata.org/entity/Q34770"
  },
  "DATE": {
    "description": "Absolute or relative dates or periods",
    "relationship": "DATE",
    "crosswalks": "date, dsPublicationDate",
    "WikiData_URI": "http://www.wikidata.org/entity/Q577"
  },
  "TIME": {
    "description": "Times smaller than a day",
    "relationship": "TIME",
    "crosswalks": "dsPublicationDate",
    "WikiData_URI": "http://www.wikidata.org/entity/Q11471"
  },
  "PERCENT": {
    "description": "Percentage (e.g., 20%)",
    "relationship": "PERCENT",
    "WikiData_URI": "http://www.wikidata.org/entity/Q11229"
  },
  "MONEY": {
    "description": "Monetary values, including unit",
    "relationship": "MONEY",
    "WikiData_URI": "http://www.wikidata.org/entity/Q1368"
  },
  "QUANTITY": {
    "description": "Measurements, as of weight or distance",
    "relationship": "QUANTITY",
    "WikiData_URI": "http://www.wikidata.org/entity/Q190900"
  },
  "ORDINAL": {
    "description": "'First', 'second', etc.",
    "relationship": "ORDINAL",
    "WikiData_URI": "http://www.wikidata.org/entity/Q243024"
  },
  "CARDINAL": {
    "description": "Numerals that do not fall under another type",
    "relationship": "CARDINAL",
    "WikiData_URI": "http://www.wikidata.org/entity/Q11372"
  }
}

        if 'nlp' in dataitem['_source']:
            self.string_data = item['_source']['nlp'].replace('’',' ')
            self.string_data = self.string_data.replace('"','')
            self.json_string = self.convert_to_json_string_part(self.string_data)
        if 'url' in dataitem['_source']:
            self.url = dataitem['_source']['url']
            
    def get_wikiuri(self, wikitype, wikiproperty='WikiData_URI'):
        if wikitype in self.spacyentities:
            return self.spacyentities[wikitype][wikiproperty]
        else:
            return
                
    def compute(self, string_data, alllabels):
        string_data = string_data.replace("'", '"')

        # Load the JSON string into a Python object
        data = json.loads(string_data)

        # Output the JSON
        json_output = json.dumps(data, indent=4)
        labels = [item['entity'] for item in data]
        alllabels+=labels
        # Count the occurrences of each label
        return alllabels

    # Function to convert the string to valid JSON format
    def convert_to_json_string(self, input_string):
        # Replace single quotes with double quotes
        json_string = re.sub(r"(?<!\\)'", '"', input_string)

        # Fix dictionary keys and values formatting
        json_string = re.sub(r'(\w+):', r'"\1":', json_string)

        # Handle cases where there are extra commas before closing brackets
        json_string = re.sub(r',(\s*[\]}])', r'\1', json_string)

        # Handle cases where there might be missing quotes around values
        json_string = re.sub(r'(?<=:)\s*([^"\[\]\{\},\s][^,}\]\s]*)', r'"\1"', json_string)
        return json_string

    def is_valid_json(self, json_string):
        try:
            # Attempt to parse the string with json.loads
            atomdata = json.loads(json_string)
            result_dict = atomdata
            return result_dict
            #return True
        except json.JSONDecodeError:
            # If an exception is raised, the string is not valid JSON
            return False

    # Function to convert the string to valid JSON format
    def convert_to_json_string_part(self, input_string):
        # Split input string by }, and then reassemble it into a valid JSON string
        input_string = input_string.replace('[','')
        input_string = input_string.replace(']','')
        parts = input_string.split("},")
        fixed_parts = []
        result = {}

        for part in parts:
            #print("PART %s" % part)
            # Add } to the end of each part except the last
            if part.strip() and not part.strip().endswith('}'):
                part += '}'
            count = len(part.split("'"))
            if count == 9:
                #if not 'TIME' in part:
                #    if not 'WORK_OF_ART' in part:
                #        fixed_parts.append(part.strip()+'\n')
                xpart = '[' + part + ']'
                xpart = xpart.replace("'", '"')
                #print(xpart)
                dataitem = self.is_valid_json(xpart)
                if dataitem:
                    #print(dataitem)
                    for k in dataitem:
                        #print(k['entity'])
                        result[k['entity']] = k['label'] #.update(dataitem)
                #print("X %s" % dataitem)
                    fixed_parts.append(part)
                #x = json.loads(xpart)
                    #print(x)
                if not '"' in part:
                    checker = re.match(r"(\w+\:)", part)
                    #if not checker:
                        #fixed_parts.append(part.strip()+'\n')
                        #print(part)
                try:
                    x = json.loads(xpart)
                    #fixed_parts.append(xpart)
                except:
                    continue
        #return result       
        # Join all parts with a comma and wrap in square brackets
        json_string = '[' + ','.join(fixed_parts) + ']'

        # Replace single quotes with double quotes
        json_string = re.sub(r"(?<!\\)'", '"', json_string)

        # Ensure all keys and string values are properly quoted
        json_string = re.sub(r'(\w+):', r'"\1":', json_string)
        json_string = re.sub(r'(?<=:)\s*([^"\[\]\{\},\s][^,}\]\s]*)', r'"\1"', json_string)
        #print(json_string)
        self.nlp = json.loads(json_string)
        #return json.loads(json_string)
        return json_string
    
    def ingraph(self):
        for x in self.nlp:
            entity_label = x['entity']
            entity_uri = URIRef(self.get_wikiuri(x['label']))
            entity_description = self.get_wikiuri(x['label'], 'description')
            if self.DEBUG:
                print("%s;%s;%s" % (x['entity'], triples.get_wikiuri(x['label']), triples.get_wikiuri(x['label'], 'description')))
            self.g.add((Literal(entity_label), RDF.type, entity_uri))
            self.g.add((Literal(entity_label), self.ns1.description, Literal(entity_description)))

