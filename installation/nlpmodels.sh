#!/bin/bash
python -c "from sentence_transformers import SentenceTransformer; \
               model = SentenceTransformer('distilbert-base-nli-mean-tokens');"
python -c "from sentence_transformers import SentenceTransformer; \
               model = SentenceTransformer('paraphrase-MiniLM-L6-v2');"
