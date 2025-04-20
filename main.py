import os
import importlib.util
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import inspect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import re

app = FastAPI()  # Initialize FastAPI without Swagger/Redoc

# Directory setup
api_folder = Path(__file__).parent / "api"
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic model for POST body
class RequestBody(BaseModel):
    data: str

# Function to extract path without query parameters
def clean_path(path: str) -> str:
    """Remove query parameters from the path while preserving the original for docs."""
    return re.sub(r'\?.*$', '', path)

# Function to load a module from a file
def load_module(file_path: str):
    module_name = os.path.basename(file_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Dynamically load API modules with enhanced metadata
def load_apis():
    routes_info = []
    for api_file in os.listdir(api_folder):
        api_path = api_folder / api_file
        if api_path.is_file() and api_file.endswith(".py"):
            try:
                module = load_module(api_path)
                
                if not hasattr(module, "meta") or not hasattr(module, "on_start"):
                    print(f"Invalid module: {api_path}")
                    continue
                
                meta = module.meta
                method = meta.get("method", "GET").lower()
                original_path = meta["path"]
                
                # Clean the path by removing query parameters for routing
                clean_route_path = clean_path(original_path)
                path = "/api" + clean_route_path
                
                # Get function parameters for documentation
                sig = inspect.signature(module.on_start)
                parameters = []
                for name, param in sig.parameters.items():
                    if name not in ['request', 'self']:  # Skip common params
                        param_info = {
                            'name': name,
                            'type': str(param.annotation),
                            'required': param.default == param.empty,
                        }
                        if not param_info['required']:
                            param_info['default'] = param.default
                        parameters.append(param_info)
                
                # Create route info with documentation data (using original path)
                route_info = {
                    "name": meta["name"],
                    "description": meta["description"],
                    "path": "/api" + original_path,  # Show full path with query params in docs
                    "method": method.upper(),
                    "author": meta.get("author", "Unknown"),
                    "version": meta.get("version", "1.0")
                }
                
                routes_info.append(route_info)
                
                # Register the route with the clean path
                if method == "post":
                    app.add_api_route(path, module.on_start, methods=["POST"])
                else:
                    app.add_api_route(path, module.on_start, methods=["GET"])
                
                print(f"Loaded route: {meta['name']} ({method.upper()} {path})")
            
            except Exception as e:
                print(f"Error loading module {api_file}: {e}")

    return routes_info

# Load all API modules
api_routes = load_apis()

# Documentation routes
@app.get("/docs", include_in_schema=False)
async def custom_docs(request: Request):
    return templates.TemplateResponse(
        "docs.html",
        {
            "request": request,
            "routes": api_routes,
            "title": "API Documentation"
        }
    )

@app.get("/docs/{endpoint_name}", include_in_schema=False)
async def endpoint_detail(request: Request, endpoint_name: str):
    endpoint = next((r for r in api_routes if r["name"] == endpoint_name), None)
    if not endpoint:
        raise HTTPException(status_code=404)
    
    return templates.TemplateResponse(
        "endpoint.html",
        {
            "request": request,
            "endpoint": endpoint,
            "title": f"Endpoint: {endpoint['name']}"
        }
    )

# API info endpoint (optional)
@app.get("/api/info")
def get_api_info():
    return {"routes": [{"name": r["name"], "description": r["description"], "path": r["path"], "method": r["method"]} for r in api_routes]}

# Home redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    raise HTTPException(status_code=302, headers={"Location": "/docs"})