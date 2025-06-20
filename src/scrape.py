import sys
import os
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
import tempfile
import shutil

def scrape_url(url: str) -> str:
    """
    Scrapes the given URL using undetected_chromedriver with a persistent profile.
    This version launches a visible browser and waits a fixed time to allow
    for manual CAPTCHA solving.
    Returns the page source HTML.
    """
    options = uc.ChromeOptions()
    # Use a temp directory for the Chrome profile so we don't pollute the workspace
    profile_dir = tempfile.mkdtemp(prefix="rym2spotify_chrome_profile_")
    options.add_argument(f"--user-data-dir={profile_dir}")
    
    driver = None
    try:
        # Using suppress_welcome_screen=True and other flags for stability
        driver = uc.Chrome(options=options, suppress_welcome_screen=True, use_subprocess=False)
        driver.get(url)

        # Give the user a generous and fixed 30-second window to solve the CAPTCHA.
        # This is more reliable than trying to detect the CAPTCHA page elements.
        print("Browser opened. You have 30 seconds to solve any CAPTCHA...")
        time.sleep(10)
        print("Time's up. Attempting to get page source.")
        
        return driver.page_source
    except TimeoutException:
        print("The page timed out after the wait. The CAPTCHA may not have been solved in time.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        raise
    finally:
        # Clean up driver and temporary profile directory
        if driver:
            driver.quit()
        shutil.rmtree(profile_dir, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        url_to_scrape = sys.argv[1]
        html_output_path = sys.argv[2]
        scrape_single_url(url_to_scrape, html_output_path)
    else:
        print("Usage: python scrape.py <URL> <output_path>")
        sys.exit(1) 