# This file is required to make Python treat the directory as a package.

# You can optionally import key components to make them easily accessible
from .app import *
from .GraphQuery import GraphQuery
from .Paracrawl import Paracrawl
from .utils import query_ollama, get_doi_from_text, get_json, form_prompt, sources, linked_data_query_constructor
from .prompts import llmprompts

# You can also define a __all__ variable to specify what gets imported with "from app import *"
__all__ = ['GraphQuery', 'Paracrawl', 'query_ollama', 'get_doi_from_text', 'get_json', 'form_prompt', 'sources', 'llmprompts', 'get_questions']

# Optionally, you can include some package-level documentation
"""
This package contains the main application and utility functions for the dataset query system.
"""