from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uuid
import asyncio

# Import your refactored, modular functions
from src.scrape import scrape_url
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

# --- In-memory storage for tasks ---
# In a production app, you'd use Redis or a database for this.
tasks = {}

def run_scraping_task(task_id: str, rym_url: str):
    """
    This function runs in the background.
    It scrapes the list and all album pages sequentially.
    """
    print(f"Background task {task_id} started for URL: {rym_url}")
    tasks[task_id] = {'status': 'processing', 'data': None, 'message': 'Scraping main list page...'}

    try:
        # 1. Scrape the main list page
        list_html = scrape_url(rym_url)
        items = parse_list_page_for_items(list_html)
        if not items:
            tasks[task_id] = {'status': 'failure', 'data': None, 'message': 'No items found on the list page.'}
            return
        
        tasks[task_id]['message'] = f'Found {len(items)} items. Processing each one...'
        
        final_list = []
        total_items = len(items)
        
        # 2. Process each item SEQUENTIALLY to avoid being flagged
        for i, item in enumerate(items):
            current_progress = f"({i+1}/{total_items})"
            if item.get('type') == 'album' and item.get('title_link'):
                tasks[task_id]['message'] = f"{current_progress} Scraping album: {item['title']}"
                try:
                    album_html = scrape_url(item['title_link'])
                    spotify_link = parse_album_page_for_spotify_link(album_html)
                    if spotify_link:
                        final_list.append(spotify_link)
                    else:
                        final_list.append(f"{item['artist']} - {item['title']}")
                except Exception as e:
                    print(f"Failed to process album {item['title']}: {e}")
                    final_list.append(f"{item['artist']} - {item['title']}") # Fallback
            elif item.get('type') == 'song':
                tasks[task_id]['message'] = f"{current_progress} Adding song: {item['title']}"
                final_list.append(f"{item['artist']} - {item['title']}")
        
        # 3. Mark task as successful
        tasks[task_id] = {'status': 'success', 'data': final_list, 'message': 'Processing complete!'}
        print(f"Background task {task_id} finished successfully.")

    except Exception as e:
        print(f"Background task {task_id} failed: {e}")
        tasks[task_id] = {'status': 'failure', 'data': None, 'message': str(e)}

# --- API Endpoints ---
@app.post("/start-scraping/", status_code=202)
async def start_scraping(request: RymUrlRequest, background_tasks: BackgroundTasks):
    """
    Starts the scraping process in the background and returns a task ID.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'data': None, 'message': 'Task received, waiting to start...'}
    
    # Run the long-running job in the background
    background_tasks.add_task(run_scraping_task, task_id, str(request.url))
    
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
