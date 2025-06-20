import sys
import os
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException
import tempfile
import shutil

class Scraper:
    """
    A class to manage a persistent undetected_chromedriver instance.
    """
    def __init__(self):
        """
        Initializes and launches the Chrome driver.
        """
        self.driver = None
        self.profile_dir = tempfile.mkdtemp(prefix="rym2spotify_chrome_profile_")
        
        try:
            options = uc.ChromeOptions()
            options.add_argument(f"--user-data-dir={self.profile_dir}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")

            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self.driver.get("about:blank") # Warm it up

        except Exception as e:
            print(f"Failed to initialize the scraper: {e}")
            self.close()
            raise

    def get_page(self, url: str) -> str:
        """
        Navigates to the given URL and returns the page source.
        Includes a one-time CAPTCHA solving window on the first call.
        """
        if not self.driver:
            raise Exception("Driver is not initialized.")

        try:
            print(f"SCRAPER LOG: Attempting to navigate to: {url}")
            self.driver.get(url)
            print(f"SCRAPER LOG: Actually landed on: {self.driver.current_url}")

            # A Cloudflare challenge will add parameters to the URL.
            if "__cf_chl_rt_tk" in self.driver.current_url:
                 print("CAPTCHA page detected. You have 30 seconds to solve it...")
                 time.sleep(30)
                 print("Time's up. Re-attempting original navigation...")
                 self.driver.get(url)
                 print(f"SCRAPER LOG: After CAPTCHA, landed on: {self.driver.current_url}")

            return self.driver.page_source
        
        except (TimeoutException, WebDriverException) as e:
            print(f"An error occurred while getting page {url}: {e}")
            raise

    def close(self):
        """
        Quits the driver and cleans up the temporary profile directory.
        """
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
        shutil.rmtree(self.profile_dir, ignore_errors=True)
