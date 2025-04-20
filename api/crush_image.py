# api/crush_image.py
from fastapi import Request, Query
from fastapi.responses import Response
from lib.crush_img import CrushImg

meta = {
    "name": "crush_image",
    "description": "Generate image using CrushChat API",
    "path": "/crush-image?prompt=&style=",
    "method": "GET"
}

async def on_start(request: Request):
    prompt = request.query_params.get("prompt")
    style = request.query_params.get("style", "anime")
    nega = request.query_params.get("negative", None)

    if not prompt:
        return {"error": "Missing prompt query parameter."}

    gen = CrushImg()
    try:
        image_bytes = await gen.gen_image(prompt=prompt, style=style, nega=nega)
        return Response(content=image_bytes, media_type="image/jpeg")
    except Exception as e:
        return {"error": str(e)}
