#!/bin/bash
python -c "from sentence_transformers import SentenceTransformer; \
               model = SentenceTransformer('distilbert-base-nli-mean-tokens');"
python -c "from sentence_transformers import SentenceTransformer; \
               model = SentenceTransformer('paraphrase-MiniLM-L6-v2');"
python -c "from transformers import GPT2Tokenizer, GPT2LMHeadModel; \
               model = GPT2LMHeadModel.from_pretrained('gpt2');" 
#python -m spacy download en_core_web_sm
