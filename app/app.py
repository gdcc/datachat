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
from app.utils import query_ollama, get_doi_from_text, get_json, form_prompt, news_prompt, sources, json_ld_to_text
from app.prompts import llmprompts, summaryprompts
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

    # Getting all app parameters
    url = st.query_params.get('url')
    dataversehost = st.query_params.get('siteUrl')
    datasetPid = st.query_params.get('datasetPid') 
    fileId = st.query_params.get('fileId')
    query = st.query_params.get('q')
    # Rewriting url if Dataverse host is set
    if dataversehost:
        url = dataversehost

    # Streamlit App
    st.title(os.environ['TITLE'])

    # Input for prompt
    description = ''
    # Add a unique key to the text_input widget
    prompt = st.text_input(os.environ['INTRO'], "")
    customprompt = ''
    if prompt:
        customprompt = prompt

    def get_questions(description, prompt):
        return llmprompts(description, prompt)
    def get_answers(description, prompt):
        return summaryprompts(description, prompt)

    # Button to trigger API call
    if st.button("Get Answer", key="get_answer_button") or query:
        if customprompt:
            query = customprompt
        # https://radio.now.museum/docs#/default/convert_resources_resources__get
        data = requests.get("%s/resources/?query=%s" % (os.environ['WIZARDURL'], query))
#        st.write(len(data.json())) 
        records = json_ld_to_text(data.json()[:10])
        llmprompt = get_answers(news_prompt(records), prompt)
#        llmprompt = get_questions(news_prompt(data.json()[:3]), prompt)
        print(llmprompt)
        response = query_ollama(llmprompt)
        st.write(response)
        
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

            st.write(doi)
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
#                            st.write(p.content)
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
