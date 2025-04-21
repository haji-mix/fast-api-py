from fastapi import Request, Query
from fastapi.responses import Response, JSONResponse
from lib.crush_img import CrushImg
gen = CrushImg()

meta = {
    "name": "crush_image",
    "description": "Generate image using CrushChat API",
    "path": "/crush-image?prompt=&style=",
    "media_type": "image/jpeg",
    "method": "GET"
}

async def on_start(request: Request, prompt: str = Query(..., description="Text prompt to generate the image"),
    style: str = Query("anime", description="Style of the image"),
    negative: str = Query(None, description="Negative prompt to avoid in the image")):
    prompt = request.query_params.get("prompt")
    style = request.query_params.get("style", "anime")
    nega = request.query_params.get("negative")

    if not prompt:
        return JSONResponse(
            content={"error": "Missing 'prompt' query parameter.", "available_styles": gen.get_supported_styles()},
            status_code=400
        )

    try:
        image_bytes = await gen.gen_image(prompt=prompt, style=style, nega=nega)
        return Response(content=image_bytes, media_type=meta["media_type"])
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to generate image: {str(e)}"},
            status_code=500
        )
