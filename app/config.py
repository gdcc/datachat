config = {}
entities = {
    "PERSON": {
      "description": "People, including fictional characters",
      "relationship": "PERSON",
      "crosswalks": "creator, author",
      "crosswalks": "authorName, authorAffiliation"
    },
    "NORP": {
      "description": "Nationalities or religious or political groups",
      "relationship": "NORP"
    },
    "FAC": {
      "description": "Buildings, airports, highways, bridges, etc.",
      "relationship": "FAC"
    },
    "ORG": {
      "description": "Companies, agencies, institutions, etc.",
      "relationship": "ORG",
      "crosswalks": "creator, author",
      "crosswalks": "authorName, authorAffiliation"
    },
    "GPE": {
      "description": "Countries, cities, states",
      "relationship": "GPE",
      "crosswalks": "locations"
    },
    "LOC": {
      "description": "Non-GPE locations, mountain ranges, bodies of water",
      "relationship": "LOC",
      "crosswalks": "locations"
    },
    "PRODUCT": {
      "description": "Objects, vehicles, foods, etc. (not services)",
      "relationship": "PRODUCT"
    },
    "EVENT": {
      "description": "Named hurricanes, battles, wars, sports events",
      "relationship": "EVENT"
    },
    "WORK_OF_ART": {
      "description": "Titles of books, songs, artworks, etc.",
      "relationship": "WORK_OF_ART"
    },
    "LAW": {
      "description": "Named documents made into laws",
      "relationship": "LAW"
    },
    "LANGUAGE": {
      "description": "Any named language",
      "relationship": "LANGUAGE"
    },
    "DATE": {
      "description": "Absolute or relative dates or periods",
      "relationship": "DATE",
      "crosswalks": "date",
      "crosswalks": "dsPublicationDate"
    },
    "TIME": {
      "description": "Times smaller than a day",
      "relationship": "TIME",
      "crosswalks": "dsPublicationDate"
    },
    "PERCENT": {
      "description": "Percentage (e.g., 20%)",
      "relationship": "PERCENT"
    },
    "MONEY": {
      "description": "Monetary values, including unit",
      "relationship": "MONEY"
    },
    "QUANTITY": {
      "description": "Measurements, as of weight or distance",
      "relationship": "QUANTITY"
    },
    "ORDINAL": {
      "description": "'First', 'second', etc.",
      "relationship": "ORDINAL"
    },
    "CARDINAL": {
      "description": "Numerals that do not fall under another type",
      "relationship": "CARDINAL"
    }
  }
