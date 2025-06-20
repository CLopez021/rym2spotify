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
    CLOUDFLARE_CHALLENGE_TEXT = "challenges.cloudflare.com"

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
            self.close()
            raise

    def get_page(self, url: str) -> str:
        """
        Navigates to the given URL and returns the page source.
        If a Cloudflare challenge is detected, it waits for manual intervention.
        """
        if not self.driver:
            raise Exception("Driver is not initialized.")

        try:
            time.sleep(2) # To avoid getting banned smh
            self.driver.get(url)
            page_source = self.driver.page_source

            if self.CLOUDFLARE_CHALLENGE_TEXT in page_source:
                 time.sleep(30)
                 self.driver.get(url)
                 page_source = self.driver.page_source

            return page_source
        
        except (TimeoutException, WebDriverException) as e:
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
