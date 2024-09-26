import streamlit as st
import re
import requests
import json
import requests
import os
from utils import query_ollama, get_doi_from_text, get_json, form_prompt, sources
from prompts import llmprompts
from Paracrawl import Paracrawl
from GraphQuery import GraphQuery

# Initialize a session state variable
if 'count' not in st.session_state:
    st.session_state.count = 0
    st.session_state.doi = ''

# Define a function to increment the counter
def increment():
    st.session_state.count += 1

## Display the counter value
#st.write(f"Current count: {st.session_state.count}")
#st.write(st.session_state.doi)

# Button to trigger increment
#st.button("Increment", on_click=increment)

url = st.query_params.get('url')
#st.write(url)

# Streamlit App
st.title(os.environ['TITLE'])

# Input for prompt
description = ''
prompt = st.text_input(os.environ['INTRO'], "")

def get_questions(description, prompt):
    return llmprompts(description, prompt)

# Button to trigger API call
if st.button("Get Response") or url:
    if not st.session_state.doi:
        if url and 'http' in url:
            doi = get_doi_from_text(url)
            if doi:
                prompt = "get intro of %s" % doi
    else:
        if not 'doi' in prompt:
            prompt+=" %s" % st.session_state.doi
    if prompt:
        #response = query_ollama(prompt)
        if url:
            doi = get_doi_from_text(url.replace('=doi',' doi'))
        else:
            doi = get_doi_from_text(prompt)
        #st.write("%s / %s" % (prompt, doi))
        if doi:
            st.session_state.doi = doi
            st.markdown("Working with dataset <a href='%s'>%s</a>." % (url, doi), unsafe_allow_html=True)
            llmprompt = get_questions(form_prompt(doi), prompt)
            #st.write(llmprompt)
            response = query_ollama(llmprompt)
            st.write(response)
        else:
            st.write("Click \"Chat\" button if you want to chat with some dataset")
            ready = False
            response = ''
            for i in range(3):
                if not ready:
                    try:
                        p = Paracrawl(prompt, sources())
                        response = "<p>Query: <i>%s</i></p>" % p.smartquery['searchquery']
                        if p.results:
                            ready = True
                            for item in p.results:
                                response+="<br>%s</br>" % item
                    except:
                        ready = False
            st.markdown(response, unsafe_allow_html=True)
    else:
       st.write("Please enter a prompt.")
#if st.button("Translate dataset"):
#    st.write("Tranlation is not available")
