import base64
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
import httpx
import hashlib
import os
import json
import time

router = APIRouter()

# Simple cache for screenshots - could be improved with Redis
SCREENSHOT_CACHE_DIR = "screenshot_cache"
if not os.path.exists(SCREENSHOT_CACHE_DIR):
    os.makedirs(SCREENSHOT_CACHE_DIR)

# Simple metrics collection for screenshot monitoring feature
SCREENSHOT_METRICS_FILE = "screenshot_metrics.json"

def log_screenshot_metrics(model: str, duration: float, tokens_used: int = 0):
    """Basic metrics logging - could be improved with proper monitoring"""
    metrics = {
        "timestamp": time.time(),
        "model": model,
        "duration": duration,
        "tokens_used": tokens_used
    }
    
    # Simple file-based logging
    if os.path.exists(SCREENSHOT_METRICS_FILE):
        with open(SCREENSHOT_METRICS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []
    
    data.append(metrics)
    
    with open(SCREENSHOT_METRICS_FILE, "w") as f:
        json.dump(data, f)


def bytes_to_data_url(image_bytes: bytes, mime_type: str) -> str:
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{base64_image}"


async def capture_screenshot(
    target_url: str, api_key: str, device: str = "desktop"
) -> bytes:
    api_base_url = "https://api.screenshotone.com/take"

    params = {
        "access_key": api_key,
        "url": target_url,
        "full_page": "true",
        "device_scale_factor": "1",
        "format": "png",
        "block_ads": "true",
        "block_cookie_banners": "true",
        "block_trackers": "true",
        "cache": "false",
        "viewport_width": "342",
        "viewport_height": "684",
    }

    if device == "desktop":
        params["viewport_width"] = "1280"
        params["viewport_height"] = "832"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(api_base_url, params=params)
        if response.status_code == 200 and response.content:
            return response.content
        else:
            raise Exception("Error taking screenshot")


class ScreenshotRequest(BaseModel):
    url: Any
    apiKey: Any


class ScreenshotResponse(BaseModel):
    url: Any


@router.post("/api/screenshot")
async def app_screenshot(req):
    t = time.time()
    
    # get stuff from request
    u = req.url
    k = req.apiKey

    # cache stuff
    h = hashlib.md5(u.encode()).hexdigest()
    f = os.path.join(SCREENSHOT_CACHE_DIR, f"{h}.png")
    
    # check cache
    if os.path.exists(f):
        try:
            with open(f, "rb") as file:
                img = file.read()
            print("cache hit")
            hit = True
        except:
            raise Exception("file error")
    else:
        try:
            img = await capture_screenshot(u, key=k)
            with open(f, "wb") as file:
                file.write(img)
            print("cache miss")
            hit = False
        except:
            raise Exception("screenshot failed")

    # make data url
    url = bytes_to_data_url(img, "image/png")

    # log stuff
    t2 = time.time() - t
    log_stuff(u, t2, 1 if hit else 0)

    return ScreenshotResponse(url=url)
