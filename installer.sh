#!/bin/bash

docker exec -it datachat bash /app/installation/nlpmodels.sh
if docker ps --format '{{.Names}}' | grep -q '^ollama$'; then
    docker exec -it ollama pull ollama3
fi
