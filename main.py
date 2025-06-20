from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import asyncio

# Import your refactored, modular functions
from src.scrape import scrape_url
from src.parse_html import parse_list_page_for_items, parse_album_page_for_spotify_link

app = FastAPI(
    title="rym2spotify API",
    description="A simple API to scrape Rate Your Music lists and find Spotify links.",
    version="1.0.0",
)

# --- Middleware ---
# Set up CORS to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for simplicity, can be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
# Define the request body for the API endpoint
class RymUrlRequest(BaseModel):
    url: HttpUrl

# --- Helper Functions ---
async def process_item(item: dict):
    """
    Asynchronously processes a single item from the list.
    If it's an album, it scrapes the album page for a Spotify link.
    """
    if item.get('type') == 'album' and item.get('title_link'):
        try:
            # Run the synchronous scrape function in a separate thread
            loop = asyncio.get_running_loop()
            album_html = await loop.run_in_executor(None, scrape_url, item['title_link'])
            spotify_link = parse_album_page_for_spotify_link(album_html)
            if spotify_link:
                return spotify_link
            else:
                # If no link, return the original format
                return f"{item['artist']} - {item['title']}"
        except Exception as e:
            print(f"Failed to process album {item['title']}: {e}")
            return f"{item['artist']} - {item['title']}" # Fallback
    elif item.get('type') == 'song':
        return f"{item['artist']} - {item['title']}"
    return None # Ignore items that don't fit the criteria

# --- API Endpoints ---
@app.post("/process-rym-list/")
async def process_rym_list(request: RymUrlRequest):
    """
    The main endpoint to process a Rate Your Music list.
    1. Scrapes the initial list URL.
    2. Parses the list to get all albums and songs.
    3. Concurrently scrapes each album page to find Spotify links.
    4. Returns a flat list of Spotify links and song titles.
    """
    try:
        print(f"Processing URL: {request.url}")
        
        # 1. Scrape the main list page
        list_html = await asyncio.get_running_loop().run_in_executor(None, scrape_url, str(request.url))
        
        # 2. Parse the list to find all items
        items = parse_list_page_for_items(list_html)
        if not items:
            raise HTTPException(status_code=404, detail="No items found on the list page. The page might be empty or a CAPTCHA was not solved.")

        print(f"Found {len(items)} items. Now processing them...")

        # 3. Process all items concurrently
        tasks = [process_item(item) for item in items]
        results = await asyncio.gather(*tasks)

        # 4. Filter out any None results and return
        final_list = [res for res in results if res]
        
        print(f"Successfully processed. Returning {len(final_list)} results.")
        return {"success": True, "data": final_list, "message": f"Successfully processed {len(final_list)} items."}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# To run this app:
# uvicorn main:app --reload
