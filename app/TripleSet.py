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
  "PER": {
    "description": "People, including fictional characters",
    "relationship": "PERSON",
    "crosswalks": "authorName, authorAffiliation",
    "WikiData_URI": "http://www.wikidata.org/entity/Q5"
  },
  "MISC" : {
    "description": "Quality of items having differing or formally unclassified traits",
    "relationship": "MISC",
    "WikiData_URI": "https://www.wikidata.org/wiki/Q2302426"    
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
    
    def singlegraph(self, data):
        # Create a new RDF graph
        g = Graph()

        # Add the data to the graph as triples
        subject = URIRef(data["_source"]["url"])  # Use the URL as the subject for the triples

        # Add properties to the graph
        g.add((subject, DC.identifier, Literal(data["_source"]["urlid"])))
        g.add((subject, DC.title, Literal(data["_source"]["title"])))
        g.add((subject, DC.date, Literal(data["_source"]["pubdate"])))
        g.add((subject, DC.source, Literal(data["_source"]["url"])))
        g.add((subject, DC.language, Literal(data["_source"]["language"])))
        g.add((subject, DC.description, Literal(data["_source"]["summary"])))
        if 'country' in data["_source"]:
            g.add((subject, DC.coverage, Literal(data["_source"]["country"])))

        # Add entities (as an example)
        entities = data["_source"]["entities"].split(", ")
        for entity in entities:
            g.add((subject, DC.subject, Literal(entity)))

        # Serialize the graph in a readable format
        if self.debug:
            print(g.serialize(format="turtle"))#.decode("utf-8"))
        return g

    def ingraph(self):
        for x in self.nlp:
            try:
                entity_label = x['entity']
                entity_uri = URIRef(self.get_wikiuri(x['label']))
                entity_description = self.get_wikiuri(x['label'], 'description')
                if self.DEBUG:
                    print("%s;%s;%s" % (x['entity'], triples.get_wikiuri(x['label']), triples.get_wikiuri(x['label'], 'description')))
                self.g.add((Literal(entity_label), RDF.type, entity_uri))
                self.g.add((Literal(entity_label), self.ns1.description, Literal(entity_description)))
            except:
                continue

    def schema_creators(self, authors, affiliations):
        creators = []
        for nameID in range(0, len(authors)):
            authorinfo = { "@type": "sc:Organisation", "name": authors[nameID]}
            try:
                if affiliations[nameID]:
                    authorinfo['affiliation'] = affiliations[nameID]
            except: 
                continue 
            creators.append(authorinfo)
        return creators
    
    def clean_name_string(self, name):
        name = name.replace('-','_')
        return re.sub("[^a-zA-Z0-9\\-_.]", "_", name)
    
    def get_fields(self, g, field_list, SEARCH='PREDICATE', REPEATED=True):
        if not isinstance(field_list, list):
            field_list = [ field_list ]
        
        for fieldname in field_list:
            #print("Lookup in graph: %s / %s" % (fieldname, field_list))
            search_property = fieldname
            if 'http' in fieldname:
                search_property = URIRef(fieldname)
            fielddata = []
            data = []
            #if self.DEBUG:
            #    print(SEARCH)
            if SEARCH == 'PREDICATE':
                data = g.triples((None, search_property, None))
            if SEARCH == 'SUBJECT':
                data = g.triples((search_property, None, None))
            if SEARCH == 'OBJECT':
                data = g.triples((None, None, search_property))
                    
            for subject, predicate, obj in data:
                #print(f"*** Subject: {subject}, Predicate: {predicate}, Object: {obj}")
                try:
                    #fielddata.append(f"{obj}")
                    #return fielddata
                    fielddata.append(obj.value)
                except:
                    fielddata.append(obj.toPython())
            if REPEATED:
                if fielddata:
                    try:
                        return fielddata[0]
                    except:
                        print(f"Error accessing the first element: {e}")
                        #return None  # Continue with warning
                #else:
                    #return ''
            else:
                if fielddata:
                    return fielddata
        return ''

    def incroissant(self, g):
        self.localmetadata = mlc.Metadata(
                    cite_as=self.get_fields(g, self.crosswalks["name"]),
                    name=self.clean_name_string(self.get_fields(g, self.crosswalks["name"])),
                    description=self.get_fields(g, self.crosswalks["description"]),
                    creators=self.schema_creators(self.get_fields(g, self.crosswalks["author"], REPEATED=False), self.get_fields(g, self.crosswalks["authoraffiliation"], REPEATED=False)),
                    url=self.get_fields(g, self.crosswalks["url"]),
                    #date_created=self.get_fields(g, self.crosswalks["date_created"], REPEATED=False),
                    #date_published=self.get_fields(g, self.crosswalks["date_published"], REPEATED=False),
                    #date_modified=self.get_fields(g, self.crosswalks["date_modified"], REPEATED=False),
                    keywords=self.get_fields(g, self.crosswalks["keywords"], REPEATED=False),
                    publisher=self.get_fields(g, self.crosswalks["publisher"], REPEATED=False),
                    #citation=get_fields(g, crosswalks["citation"]),
                    license=self.get_fields(g, self.crosswalks["license"], REPEATED=False),
                    sd_licence=self.get_fields(g, self.crosswalks["license"], REPEATED=False),
                    version=self.get_fields(g, self.crosswalks["version"], REPEATED=True),
                    #distribution=self.distributions,
                    #record_sets=self.record_sets,
                    in_language=self.get_fields(g, self.crosswalks["in_language"], REPEATED=False),
                )
        metadatajson = self.localmetadata.to_json()
        return metadatajson #self.localmetadata

