import pytest
from backend.image_generation import core
from bs4 import BeautifulSoup
import asyncio


def test_extract_dimensions():
    url = "https://placehold.co/300x200"
    assert core.extract_dimensions(url) == (300, 200)
    url2 = "https://example.com/image.png"
    assert core.extract_dimensions(url2) == (100, 100)
    url3 = "https://img/512x512/other"
    assert core.extract_dimensions(url3) == (512, 512)


def test_create_alt_url_mapping():
    html = '''<html><body>
        <img src="https://img.com/a.png" alt="cat"/>
        <img src="https://img.com/b.png" alt="dog"/>
        <img src="https://placehold.co/300x200" alt="placeholder"/>
    </body></html>'''
    mapping = core.create_alt_url_mapping(html)
    assert mapping == {"cat": "https://img.com/a.png", "dog": "https://img.com/b.png"}

@pytest.mark.asyncio
async def test_generate_images(monkeypatch):
    # HTML with two placeholder images
    html = '''<html><body>
        <img src="https://placehold.co/300x200" alt="cat"/>
        <img src="https://placehold.co/400x400" alt="dog"/>
        <img src="https://img.com/real.png" alt="real"/>
    </body></html>'''
    # Mock process_tasks to return fake URLs
    async def mock_process_tasks(prompts, api_key, base_url, model):
        return [f"https://fakeimg.com/{p}.png" for p in prompts]
    monkeypatch.setattr(core, "process_tasks", mock_process_tasks)
    # No cache
    image_cache = {}
    result_html = await core.generate_images(html, api_key="key", base_url=None, image_cache=image_cache)
    soup = BeautifulSoup(result_html, "html.parser")
    imgs = soup.find_all("img")
    # The first two should have replaced src and width/height
    assert imgs[0]["src"] == "https://fakeimg.com/cat.png"
    assert imgs[0]["width"] == "300"
    assert imgs[0]["height"] == "200"
    assert imgs[1]["src"] == "https://fakeimg.com/dog.png"
    assert imgs[1]["width"] == "400"
    assert imgs[1]["height"] == "400"
    # The third should be unchanged
    assert imgs[2]["src"] == "https://img.com/real.png"

@pytest.mark.asyncio
async def test_generate_images_with_cache(monkeypatch):
    html = '''<html><body>
        <img src="https://placehold.co/300x200" alt="cat"/>
        <img src="https://placehold.co/400x400" alt="dog"/>
    </body></html>'''
    # Only 'cat' is in cache
    image_cache = {"cat": "https://cached.com/cat.png"}
    async def mock_process_tasks(prompts, api_key, base_url, model):
        # Only 'dog' will be generated
        return ["https://fakeimg.com/dog.png"]
    monkeypatch.setattr(core, "process_tasks", mock_process_tasks)
    result_html = await core.generate_images(html, api_key="key", base_url=None, image_cache=image_cache)
    soup = BeautifulSoup(result_html, "html.parser")
    imgs = soup.find_all("img")
    assert imgs[0]["src"] == "https://cached.com/cat.png"
    assert imgs[1]["src"] == "https://fakeimg.com/dog.png"
