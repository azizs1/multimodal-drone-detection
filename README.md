# Multimodal Drone Detection
**Authors:** Chia-Yu Chang, Yu-Chieh Cheng, Li-Chieh Kung, Ethan Mauger, Aziz Shaik
**Course:** CS 5934: Capstone Design (Spring 2026)

This MEng capstone project aims to build a drone detection system with an AI-enabled multimodal approach.

## How to Use
This repository essentially contains three smaller repositories within it, separated based on the container that the components will be running on. Two containers, `frontend` and `backend` run on <WHERE DO THESE RUN, PROBS LAPTOP>, while the machine learning and sensor ingestion both run within the same container on a Jetson Nano.

For the backend, machine learning, and sensor ingestion components, `uv` is used as the package manager.
>NOTE: Run `uv sync` to download any dependencies within a virtual environment. When running Python files, you must use `uv run python sample.py`.

### Frontend
#### Development
\<how to initialize this for dev\>
#### Deployment
\<how to deploy the docker container for this\>
### Backend
#### Development

\<how to initialize this for dev\>
#### Deployment
\<how to deploy the docker container for this\>
### Jetson
#### Development
\<how to initialize this for dev\>
#### Deployment
\<how to deploy the docker container for this\>
