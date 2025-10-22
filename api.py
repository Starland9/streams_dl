
import uvicorn
from fastapi import FastAPI, Body, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from selenium import webdriver
from uqload_dl import UQLoad
import os
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from providers.french_stream import FrenchStreamProvider
from providers.papadustream import PapaduStreamProvider
from providers.flemmix import FlemmixProvider
import undetected_chromedriver as uc

# --- Constants ---
DOWNLOADS_DIR = os.path.join(os.getcwd(), "downloads")

# --- Selenium WebDriver Setup ---
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
# driver = webdriver.Chrome(
#     service=ChromeService(ChromeDriverManager().install()), options=chrome_options
# )


driver = uc.Chrome(options=chrome_options)

# Initialize providers
providers = {
    "papadustream": PapaduStreamProvider(driver),
    "french-stream": FrenchStreamProvider(driver),
    "flemmix": FlemmixProvider(driver),
}

# Default provider
default_provider = "french-stream"


# --- FastAPI App ---
app = FastAPI(
    title="Streaming API",
    description="An API to search, get video links, and download from multiple streaming providers (Flemmix, PapaduStream, French-Stream).",
    version="1.0.0",
)


async def download_video_in_background(video_url: str):
    """
    Downloads a video from a UQload URL in the background.
    """
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)

    try:
        uqload = UQLoad(url=video_url, output_dir=DOWNLOADS_DIR)
        # Run the blocking download call in a thread pool as well
        await run_in_threadpool(uqload.download)
        print(f"Finished downloading {video_url}")
    except Exception as e:
        print(f"Error downloading {video_url}: {e}")


# --- API Endpoints ---

@app.get("/providers", summary="List available providers")
async def list_providers():
    """
    Returns the list of available streaming providers.
    """
    return {
        "providers": list(providers.keys()),
        "default": default_provider
    }


@app.get("/search", summary="Search for media")
async def search(query: str, provider_name: str = default_provider):
    """
    Searches for movies and series on the specified streaming provider.

    - **query**: The search term (e.g., "The Matrix", "La Casa de Papel").
    - **provider_name**: The provider to use (papadustream, french-stream, or flemmix). Default is flemmix.
    """
    if provider_name not in providers:
        return {
            "error": f"Invalid provider. Available providers: {', '.join(providers.keys())}"
        }

    provider = providers[provider_name]
    search_results = await run_in_threadpool(provider.search_media, query)
    return {"results": [media.to_dict() for media in search_results]}


@app.post("/get-videos", summary="Get video links from a media URL")
async def get_videos(
    media_url: str = Body(..., embed=True,
                          description="The URL of the media page from a search result."),
    provider_name: str = Body(default_provider, embed=True,
                              description="The provider name (papadustream, french-stream, or flemmix).")
):
    """
    Takes a media page URL and scrapes it to find direct UQload video links.
    """
    if provider_name not in providers:
        return {
            "error": f"Invalid provider. Available providers: {', '.join(providers.keys())}"
        }

    provider = providers[provider_name]
    video_results = await provider.get_uqvideos_from_media_url(media_url)
    return {"results": [video.to_dict() for video in video_results]}


@app.post("/download", summary="Download a video in the background")
async def download(background_tasks: BackgroundTasks, video_url: str = Body(..., embed=True, description="The UQload page URL of the video to download.")):
    """
    Starts a background task to download a video from its UQload URL.
    The video will be saved in the `downloads` directory on the server.
    """
    background_tasks.add_task(download_video_in_background, video_url)
    return {"message": "Download started in background.", "video_url": video_url}


# --- Lifecycle Events ---

@app.on_event("startup")
def startup_event():
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)


@app.on_event("shutdown")
def shutdown_event():
    driver.quit()


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8095, reload=True)
