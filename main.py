from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uuid
import asyncio
import re
import time

# Import your refactored, modular functions
from src.scrape import Scraper
from src.parse_html import parse_list_page_for_items, parse_album_page_for_spotify_link

app = FastAPI(
    title="rym2spotify API",
    description="An API to handle long-running scraping tasks for Rate Your Music lists.",
    version="2.0.0",
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
    scrape_albums: bool = False # Add new field with a default

# --- In-memory storage for tasks ---
# In a production app, you'd use Redis or a database for this.
tasks = {}

def run_scraping_task(task_id: str, rym_url: str, scrape_albums: bool):
    """
    This function runs in the background.
    It scrapes all pages of a RYM list and, if requested, all album pages sequentially.
    """
    print(f"Background task {task_id} started for URL: {rym_url} (Scrape Albums: {scrape_albums})")
    scraper = None
    try:
        tasks[task_id] = {'status': 'processing', 'message': 'Initializing browser...'}
        scraper = Scraper()
        
        base_url_match = re.match(r"(https://rateyourmusic\.com/list/[^/]+/[^/]+)", rym_url)
        if not base_url_match:
            raise ValueError("Invalid RYM list URL format.")
        base_url = base_url_match.group(1)

        all_items = []
        page_number = 1
        
        # This will be the first page loaded, triggering the CAPTCHA wait if needed.
        first_page_url = f"{base_url}/1/"
        tasks[task_id]['message'] = 'Scraping list page 1... (check browser for CAPTCHA)'
        print(f"Scraping list page 1... (check browser for CAPTCHA)")
        list_html = scraper.get_page(first_page_url)
        page_items = parse_list_page_for_items(list_html)

        if not page_items:
            print(f"No items found on the first page.")
            tasks[task_id] = {'status': 'success', 'data': [], 'message': 'Scraping complete. No items found on the first page.'}
            return
            
        all_items.extend(page_items)
        page_number += 1

        while True:
            print(f"Scraping list page {page_number}fsdfsfdsfsdfsdf..")
            tasks[task_id]['message'] = f'Scraping list page {page_number}...'
            paginated_url = f"{base_url}/{page_number}/"
            
            list_html = scraper.get_page(paginated_url)
            if list_html is None:
                break
            try:
                page_items = parse_list_page_for_items(list_html)
            except Exception as e:
                break
            if not page_items:
                break
            
            all_items.extend(page_items)
            page_number += 1
            time.sleep(1) # Be polite

        tasks[task_id]['message'] = f'Found {len(all_items)} items. Processing...'
        
        final_list = []
        for i, item in enumerate(all_items):
            progress = f"({i+1}/{len(all_items)})"
            if scrape_albums and item.get('type') == 'album' and item.get('title_link'):
                tasks[task_id]['message'] = f"{progress} Scraping album: {item['title']}"
                try:
                    time.sleep(1) # Be polite
                    album_html = scraper.get_page(item['title_link'])
                    spotify_link = parse_album_page_for_spotify_link(album_html)
                    final_list.append(spotify_link or f"{item['artist']} - {item['title']}")
                except Exception as e:
                    print(f"Failed to process album {item['title']}: {e}")
                    final_list.append(f"{item['artist']} - {item['title']}") # Fallback
            else:
                tasks[task_id]['message'] = f"{progress} Adding: {item['title']}"
                final_list.append(f"{item['artist']} - {item['title']}")
        
        tasks[task_id] = {'status': 'success', 'data': final_list, 'message': 'Processing complete!'}
        print(f"Background task {task_id} finished successfully.")

    except Exception as e:
        print(f"Background task {task_id} failed: {e}")
        tasks[task_id] = {'status': 'failure', 'message': str(e)}
    finally:
        if scraper:
            scraper.close()
            print(f"Scraper for task {task_id} has been closed.")

# --- API Endpoints ---
@app.post("/start-scraping/", status_code=202)
async def start_scraping(request: RymUrlRequest, background_tasks: BackgroundTasks):
    """
    Starts the scraping process in the background and returns a task ID.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'data': None, 'message': 'Task received, waiting to start...'}
    
    # Run the long-running job in the background
    background_tasks.add_task(run_scraping_task, task_id, str(request.url), request.scrape_albums)
    
    return {"task_id": task_id, "message": "Scraping task started."}

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Allows the frontend to poll for the status of a background task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task

# To run this app:
# uvicorn main:app --reload
