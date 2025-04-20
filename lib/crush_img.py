# lib/crush_img.py
import httpx
import asyncio

class CrushImg:
    def __init__(self):
        self.available_styles = ["realistic", "anime"]
        self.base_url = "https://crushchat.app/api/v2/generate/image"

    async def gen_image(self, prompt, style="realistic", nega=None):
        if style not in self.available_styles:
            raise ValueError(f"Invalid style. Available styles: {', '.join(self.available_styles)}")

        payload = {
            "onlyPrompt": True,
            "modelType": style,
            "prompt": prompt,
            "negativePrompt": nega,
            "characterName": "Rhea",
            "conversation": [],
            "userName": "User",
            "autoGen": False
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://crushchat.app",
            "Referer": "https://crushchat.app/images/playground"
        }

        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(self.base_url, json=payload, headers=headers)
                res.raise_for_status()
                return await self._gen_status(client, res.json()["id"])
            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to generate image request: {e}")

    async def _gen_status(self, client, image_id):
        status_url = f"{self.base_url}/status/{image_id}"

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://crushchat.app/images/playground"
        }

        for _ in range(20):  # Max 20 seconds
            res = await client.get(status_url, headers=headers)
            data = res.json()
            if data["status"] == "completed":
                image_url = data["reply"]["output"][0]["image"]
                image_res = await client.get(image_url)
                return image_res.content  # raw image bytes
            await asyncio.sleep(1)

        raise TimeoutError("Image generation timed out")

    def get_supported_styles(self):
        return self.available_styles
