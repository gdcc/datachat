import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import streamlit as st
import re
import requests
import json

# Use absolute imports
from app.utils import query_ollama, get_doi_from_text, get_json, form_prompt, sources
from app.prompts import llmprompts
from app.Paracrawl import Paracrawl
from app.GraphQuery import GraphQuery

def main():
    # Initialize a session state variable
    if 'count' not in st.session_state:
        st.session_state.count = 0
        st.session_state.doi = ''

    # Define a function to increment the counter
    def increment():
        st.session_state.count += 1

    url = st.query_params.get('url')

    # Streamlit App
    st.title(os.environ['TITLE'])

    # Input for prompt
    description = ''
    # Add a unique key to the text_input widget
    prompt = st.text_input(os.environ['INTRO'], "")

    def get_questions(description, prompt):
        return llmprompts(description, prompt)

    # Button to trigger API call
    if st.button("Get Response", key="get_response_button") or url:
        if not st.session_state.doi:
            if url and 'http' in url:
                doi = get_doi_from_text(url)
                if doi:
                    prompt = f"get intro of {doi}"
        else:
            if 'doi' not in prompt:
                prompt += f" {st.session_state.doi}"
        if prompt:
            if url:
                (host, doi) = get_doi_from_text(url) #url.replace('=doi',' doi'))
            else:
                (host, doi) = get_doi_from_text(prompt)

            if host:
                os.environ['hostname'] = host

            if doi:
                st.session_state.doi = doi
                st.markdown(f"Working with dataset <a href='{url}'>{doi}</a>.", unsafe_allow_html=True)
                llmprompt = get_questions(form_prompt(doi), prompt)
                response = query_ollama(llmprompt)
                st.write(response)
            else:
                st.write("Click \"Chat\" button if you want to chat with some dataset")
                ready = False
                response = ''
                for i in range(3):
                    if not ready:
                        #try:
                        if not ready:
                            p = Paracrawl(prompt, sources())
                            response = f"<p>Query: <i>{p.smartquery['searchquery']}</i></p>"
                            if p.results:
                                ready = True
                                for item in p.results:
                                    response += f"<br>{item}</br>"
                        #except:
                            #ready = False
                st.markdown(response, unsafe_allow_html=True)
        else:
           st.write("Please enter a prompt.")

if __name__ == "__main__":
    main()
