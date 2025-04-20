# api/test.py

meta = {
    "name": "Test Endpoint",
    "path": "/test?q=hello",
    "method": "GET",
    "description": "Test endpoint with query param",
}

from fastapi import Query

def on_start(q: str = Query(...)):
    return {"message": f"You sent: {q}"}
