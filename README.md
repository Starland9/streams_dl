# Streams DL - Multi-Provider Streaming API

A FastAPI-based application for searching and downloading videos from multiple French streaming sites.

## Supported Providers

1. **Flemmix** (formerly Wiflix) - `flemmix`
   - Base URL: https://flemmix.wiki/
   - Default provider

2. **PapaduStream** - `papadustream`
   - Base URL: https://papadustream.credit/

3. **French Stream** - `french-stream`
   - Base URL: https://www.french-streaming.tv/

## Installation

```bash
pip install -r requirements.txt
pip install undetected-chromedriver
```

## Usage

### Running the API

```bash
python api.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. List Providers

**GET** `/providers`

Returns the list of available streaming providers.

**Response:**
```json
{
  "providers": ["papadustream", "french-stream", "flemmix"],
  "default": "flemmix"
}
```

### 2. Search for Media

**GET** `/search?query={search_term}&provider_name={provider}`

Search for movies or series.

**Parameters:**
- `query` (required): Search term (e.g., "Futurama", "The Matrix")
- `provider_name` (optional): Provider to use (default: "flemmix")

**Example:**
```bash
curl "http://localhost:8000/search?query=Futurama&provider_name=flemmix"
```

**Response:**
```json
{
  "results": [
    {
      "title": "Futurama",
      "url": "https://flemmix.wiki/serie/futurama",
      "image_url": "https://..."
    }
  ]
}
```

### 3. Get Video Links

**POST** `/get-videos`

Extract video links from a media page.

**Body:**
```json
{
  "media_url": "https://flemmix.wiki/serie/futurama",
  "provider_name": "flemmix"
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "Episode 1",
      "url": "https://uqload.cx/...",
      "duration": "...",
      "resolution": "720p",
      "size_in_bytes": 123456789
    }
  ]
}
```

### 4. Download Video

**POST** `/download`

Start a background download task.

**Body:**
```json
{
  "video_url": "https://uqload.cx/embed-xyz.html"
}
```

## Testing Individual Providers

### Test Flemmix Provider

```bash
python test_flemmix.py "Futurama"
```

### Test PapaduStream Provider

```bash
python test_papadustream.py
```

## Architecture

### Provider Structure

Each provider implements the `AbstractProvider` interface:

```python
class AbstractProvider:
    def search_media(self, text: str) -> list[Media]:
        """Search for media and return results"""
        raise NotImplementedError

    async def get_uqvideos_from_media_url(self, url: str) -> list[UqVideo]:
        """Extract video links from a media page"""
        raise NotImplementedError
```

### Adding a New Provider

1. Create a new file in `providers/` (e.g., `providers/new_site.py`)
2. Implement the `AbstractProvider` interface
3. Add the provider to `api.py`:

```python
from providers.new_site import NewSiteProvider

providers = {
    # ... existing providers
    "new-site": NewSiteProvider(driver),
}
```

## Models

### Media

Represents a movie or series search result:

```python
class Media:
    title: str           # Title of the media
    url: str | None      # URL to the media page
    image_url: str | None  # Thumbnail/poster URL
```

### UqVideo

Represents a video with metadata:

```python
class UqVideo:
    duration: str
    image_url: str
    resolution: str
    size_in_bytes: int
    title: str
    type: str
    url: str            # Direct video URL
    html_url: str       # UQload page URL
```

## Development

### Code Style

The project follows these patterns:
- Use type hints for all function parameters and returns
- Use XPath for web scraping
- Handle exceptions gracefully
- Use `run_in_threadpool` for blocking operations
- Normalize URLs to absolute paths

### Key Technologies

- **FastAPI**: Web framework
- **Selenium**: Web scraping with JavaScript rendering
- **undetected-chromedriver**: Bypass bot detection
- **UQLoad**: Video extraction library

## Notes

- The Flemmix provider is designed to be robust with multiple fallback XPath patterns
- All providers normalize UQload URLs to ensure uniqueness
- The API uses a single shared Chrome driver instance for efficiency
- Downloads are handled in background tasks

## Legal Notice

This tool is for educational purposes only. Always respect copyright laws and terms of service of the streaming sites.
