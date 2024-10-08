import networkx as nx
from app.config import config

class GraphQuery():
    def __init__(self, ner, debug=False):
        self.allfields = ['title', 'dsDescriptionValue', 'keywordValue', 'authorName']
        self.params = {}
        forbidden = ['data', 'datasets', 'dataset', 'not specified', 'NA', 'N/A', 'None', 'statistics', 'data set']
        for item in forbidden:
            if item.lower() in ner:
                ner.pop(item)
        self.ner = ner
        self.values = []
        self.G = self.create_query_graph(self.ner)

    def get_keys_by_value(self, value=None):
        """
        Get all keys associated with a specific value in the ner dictionary.

        Args:
            ner (dict): The dictionary containing the NER data.
            value (str): The specific value to search for.

        Returns:
            list: A list of keys that match the specified value.
        """
        return [key for key, val in self.ner.items() if val == value]

    def get_ner_value(self, key=None):
        """
        Get the value for a specific key from the ner dictionary.
        If the key is not provided, return a list of unique values.

        Args:
            ner (dict): The dictionary containing the NER data.
            key (str, optional): The specific key to retrieve the value for.

        Returns:
            str or list: The value associated with the key, or a list of unique values if no key is provided.
        """
        if key is not None:
            return self.ner.get(key, None)  # Return the value for the specific key, or None if not found
        else:
            return list(set(self.ner.values()))  # Return unique values if no key is specified

    def create_query_graph(self, ner):
        # Create a directed graph
        G = nx.DiGraph()

        self.values = list(set(ner.values()))

        # Add nodes for the query terms
        for entity in ner:
            G.add_node(entity)

       # Group entities by their relationship types
        relation_dict = {}
        for entity, rel in ner.items():
            if rel not in relation_dict:
                relation_dict[rel] = []
            relation_dict[rel].append(entity)

        # Add edges based on relationships
        for rel, entities in relation_dict.items():
            if len(entities) > 1:
                # If multiple entities share the same relationship, connect them with OR
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        G.add_edge(entities[i], entities[j], relation='OR')
                        G.add_edge(entities[j], entities[i], relation='OR')
            else:
                # If only one entity, connect it with AND to others
                for entity in entities:
                    for other_entity in ner.keys():
                        if entity != other_entity:
                            G.add_edge(entity, other_entity, relation='AND')

        return G

    def generate_solr_query(self):
        G = self.G
        dataset = "type"

        self.scope = self.values #['date'] #,'loc','date']
        for param in self.scope:
            subject_group = []
            for subjectvar in self.get_keys_by_value(param):
                subjects = [node for node in G.neighbors(subjectvar)]
                for subject in self.allfields:
                    subject_group.append(f'{subject}:"{subjectvar}"')

                    # Construct subject groups with the correct relationship type
                    for objectvar in subjects:
                        # Check the relationship type
                        #print(subject)
                        relation = G[subjectvar][objectvar]["relation"]
                        if relation == 'OR':
                            if not "%s:%s" % (subject, objectvar) in subject_group:
                                subject_group.append(f'{subject}:"{objectvar}"')
            self.params[param] = subject_group

        # Combine subjects with OR
        #print(subject_group)
        if 'keywords' in self.params:
            subject_group = set(self.params['keywords'])
            subject_group_str = " OR ".join(subject_group)
        else:
            subject_group_str = ''
            
        if 'locations' in self.params:
            loc_group = set(self.params['locations'])
            loc_group_str = " OR ".join(loc_group)
        else:
            loc_group_str = ''
            
        if 'date' in self.params:
            date_group = set(self.params['date'])
            date_group_str = " OR ".join(date_group)
        else:
            date_group_str = ''   

        author_group_str = ''
        for newfilter in self.params:
            if 'author' in newfilter:
                author_group = set(self.params[newfilter])
                author_group_str = " OR ".join(author_group)

        query_conditions = f'{dataset}:"dataset"'
        if subject_group_str:
            query_conditions+=f' AND ({subject_group_str})'
        if loc_group_str:
            query_conditions+=f' AND ({loc_group_str})'
        if date_group_str:
            query_conditions+=f' AND ({date_group_str})'
        if author_group_str:
            query_conditions+=f' AND ({author_group_str})'
        return query_conditions
