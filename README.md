# rym2spotify

Extract albums and songs from Rate Your Music lists and format them for easy import into Spotify playlists via [Spotlistr](https://www.spotlistr.com/search/textbox).

## How it works

This project uses a FastAPI backend to scrape RYM lists. A simple vanilla JS frontend provides the user interface. When you submit a RYM list URL, a Playwright browser may open to solve a CAPTCHA if required by Cloudflare.

The scraper extracts track or album information and displays it in the frontend, ready to be copied and pasted.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/CLopez021/rym2spotify.git
    cd rym2spotify
    ```

## Running the Application

To start the application, simply run the `run.py` script:

```bash
uv run run.py
```

This will:
1.  Start the FastAPI backend server.
2.  Open the application's frontend in your default web browser.

You can then paste a RYM list URL into the input field and start processing.

To stop the server, press `Ctrl+C` in the terminal where the script is running.
