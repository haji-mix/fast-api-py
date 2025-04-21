# api/test.py

meta = {
    "name": "test",
    "path": "/test?q=hello",
    "method": "GET",
    "description": "Test endpoint with query param",
}

from fastapi import Query

def on_start(q: str = Query(..., description="A greeting message to be echoed back")):
    return {"message": f"You sent: {q}"}
