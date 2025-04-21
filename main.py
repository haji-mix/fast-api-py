import os
import importlib.util
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import inspect
import re
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response

app = FastAPI(docs_url="/lazy-docs", openapi_url="/openapi.json")

# Directory setup
api_folder = Path(__file__).parent / "api"
templates = Jinja2Templates(directory="templates")

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
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        raise ImportError(f"Error loading module {file_path}: {e}")

# Dynamically load API modules with enhanced metadata
def load_apis():
    routes_info = []
    for api_file in os.listdir(api_folder):
        api_path = api_folder / api_file
        if api_path.is_file() and api_file.endswith(".py"):
            try:
                module = load_module(str(api_path))
                
                if not hasattr(module, "meta") or not hasattr(module, "on_start"):
                    print(f"Warning: Module {api_path} does not contain 'meta' or 'on_start'. Skipping.")
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
                    if name not in ['request', 'self']:
                        param_info = {
                            'name': name,
                            'type': str(param.annotation),
                            'required': param.default == param.empty,
                        }
                        if not param_info['required']:
                            param_info['default'] = param.default
                        parameters.append(param_info)
                
                # Get response media type from meta, default to application/json
                response_media_type = meta.get("media_type", "application/json")
                
                # Define responses for Swagger documentation
                responses = {
                    200: {
                        "content": {response_media_type: {}},
                        "description": "Successful response"
                    }
                }
                
                # Register the route with the appropriate response class
                if method == "post":
                    app.add_api_route(
                        path,
                        module.on_start,
                        methods=["POST"],
                        responses=responses,
                        response_class=Response
                    )
                else:
                    app.add_api_route(
                        path,
                        module.on_start,
                        methods=["GET"],
                        responses=responses,
                        response_class=Response
                    )
                
                # Create route info with documentation data (using original path)
                route_info = {
                    "name": meta["name"],
                    "description": meta["description"],
                    "path": "/api" + original_path,
                    "method": method.upper(),
                    "author": meta.get("author", "Kenneth Panio"),
                    "version": meta.get("version", "1.0"),
                    "parameters": parameters,
                    "media_type": response_media_type
                }
                
                routes_info.append(route_info)
                
                print(f"Loaded route: {meta['name']} ({method.upper()} {path})")
            
            except ImportError as e:
                print(f"Error during module loading {api_file}: {e}")

    return routes_info

# Load all API modules
api_routes = load_apis()

# Home redirect to Swagger UI Lazy Docs
@app.get("/", include_in_schema=False)
async def root():
    raise HTTPException(status_code=302, headers={"Location": "/lazy-docs"})

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)