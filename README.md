# DataChat - AI powered app for data
DataChat is multilingual Open-Source natural language interface for Dataverse and other data platforms with experimental Graph AI implementation for Croissant ML support.

# Acknowledgements
DataChat is in active development, please find below the acknowledgements for resources and contributions from the ongoing projects.

Region | Project  | Funding information | Component |
| ------------- | ------------- | ------------- | ------------- |
| Netherlands | [ODISSEI](http://odissei-data.nl) | NWO grant number 184.035.014 | [ODISSEI Portal](http://portal.odissei.nl) |
| Netherlands | [SSHOC.nl](https://www.nwo.nl/projecten/184036020) | NWO grant number 184.036.020 | SSHOC.nl data platform |
| France | [Now.Museum](https://now.museum/en/) | Université Paris Cité microgrant | [Now.Museum Timeline](http://time.now.museum) |
| European Union | [MuseIT](https://www.muse-it.eu) | HORIZON-CL2-2021-HERITAGE-01-04, Grant agreement #101061441 | AI for people with disabilities |

# Quick start
```
cp env_sample .env
docker-compose up -d
```

For local deployment of llama3:
```
docker exec -it ollama /bin/bash
ollama pull llama3
```
Demo of the app below:

![Demo of Feature](docs/demo.gif)

### Citation

For academic use please cite this work as:

``
Tykhonov, Vyacheslav. (2024). Building natural language interface for Dataverse network based on Croissant ML standard. Zenodo. https://doi.org/10.5281/zenodo.13842869
``
