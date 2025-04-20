#!/bin/bash

# Run the FastAPI server with auto-reload enabled
pip install -r requirements.txt
uvicorn main:app --reload
