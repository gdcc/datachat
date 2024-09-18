import streamlit as st
import re
import requests
import json
import requests
import os
from utils import query_ollama, get_doi_from_text, get_json, form_prompt
from prompts import llmprompts

# Streamlit App
st.title(os.environ['TITLE'])

# Input for prompt
description = ''
prompt = st.text_input(os.environ['INTRO'], "")

def get_questions(description, prompt):
    return llmprompts(description, prompt)

# Button to trigger API call
if st.button("Get Response"):
    if prompt:
        #response = query_ollama(prompt)
        doi = get_doi_from_text(prompt)
        st.write("Getting dataset %s" % doi)
        llmprompt = get_questions(form_prompt(doi), prompt)
        #st.write(llmprompt)
        response = query_ollama(llmprompt)
        st.write(response)
    else:
       st.write("Please enter a prompt.")
if st.button("Translate dataset"):
    st.write("Tranlation is not available")
