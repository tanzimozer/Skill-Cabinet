"""
Selenium web scraper scaffold with detection evasion.
Copy and adapt for your target website.

Key features:
- Jittered request delays (avoids timing patterns)
- Dynamic rate-limit detection (backs off before hitting limits)
- Retry logic with exponential backoff
- Robust DOM selector fallbacks (3+ strategies per element)
- Session persistence (Chrome profile caching)
- Comprehensive logging
"""

import json
import time
import logging
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import config

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# === RATE LIMITING ===
class RateLimitTracker:
    """Track requests in rolling window; detect approaching rate limits."""
    
    def __init__(self, window_seconds=300, max_requests=40):
        self.window = window_seconds
        self.max_requests = max_requests
        self.requests = []
    
    def add_request(self):
        """Log a request timestamp."""
        now = time.time()
        # Purge old requests outside window
        self.requests = [r for r in self.requests if now - r < self.window]
        self.requests.append(now)
    
    def should_backoff(self):
        """True if approaching rate limit."""
        return len(self.requests) >= self.max_requests
    
    def count(self):
        """Current request count in window."""
        return len(self.requests)


# === MAIN SCRAPER ===
class WebScraper:
    """Headless Selenium scraper with detection evasion."""
    
    def __init__(self):
        self.driver = None
        self.results = []
        self.rate_limiter = RateLimitTracker(
            window_seconds=config.RATE_LIMIT_WINDOW,
            max_requests=config.RATE_LIMIT_MAX
        )
        self.max_retries = 3
    
    def init_driver(self):
        """Initialize headless Chrome with realistic settings."""
        chrome_options = Options()
        
        if config.HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Avoid headless detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Realistic window size
        chrome_options.add_argument(f"--window-size={config.WINDOW_SIZE[0]},{config.WINDOW_SIZE[1]}")
        
        # Stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Real user agent
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # ** CRITICAL:** Session persistence
        chrome_options.add_argument("--user-data-dir=/tmp/web-scraper-profile")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(20)
        
        logger.info("Chrome driver initialized")
    
    def jittered_delay(self, base=None):
        """Sleep with random jitter (avoid timing patterns)."""
        if base is None:
            base = config.REQUEST_DELAY
        
        jitter = base + random.uniform(-1, 2)
        time.sleep(max(2, jitter))
    
    def should_continue(self):
        """Check rate limit before next request."""
        if self.rate_limiter.should_backoff():
            backoff_time = config.RATE_LIMIT_BACKOFF + random.uniform(0, 60)
            logger.warning(
                f"Rate limit detected ({self.rate_limiter.count()} requests). "
                f"Backing off for {backoff_time:.0f}s"
            )
            time.sleep(backoff_time)
            self.rate_limiter.requests = []  # Reset counter
            return True
        return True
    
    def navigate_to(self, url):
        """Navigate to URL with rate-limit checking."""
        if not self.should_continue():
            return False
        
        try:
            self.driver.get(url)
            self.rate_limiter.add_request()
            self.jittered_delay()
            return True
        except Exception as e:
            logger.error(f"Navigation failed to {url}: {e}")
            return False
    
    def extract_with_fallback(self, xpath_strategies, attribute="text"):
        """
        Extract element using multiple XPath fallback strategies.
        
        Args:
            xpath_strategies: List of (xpath, attribute_name) tuples
            attribute: 'text' for element.text, or attribute name like 'href'
        
        Returns:
            Extracted value or None if all strategies fail
        """
        for xpath, attr in xpath_strategies:
            try:
                elem = self.driver.find_element(By.XPATH, xpath)
                
                if attr == "text":
                    value = elem.text.strip()
                else:
                    value = elem.get_attribute(attr)
                
                if value:
                    return value
            except:
                continue
        
        return None
    
    def scrape_item(self, item_id):
        """
        Scrape a single item with retry logic.
        
        Override this method for your target.
        """
        for attempt in range(self.max_retries):
            try:
                url = f"https://example.com/item/{item_id}"
                if not self.navigate_to(url):
                    return None
                
                # Example: extract title with fallbacks
                title_strategies = [
                    ("//h1[@class='title']", "text"),
                    ("//h1", "text"),
                    ("//title", "text"),
                ]
                title = self.extract_with_fallback(title_strategies)
                
                # Example: extract description
                desc_strategies = [
                    ("//div[@class='description']", "text"),
                    ("//article//p", "text"),
                ]
                description = self.extract_with_fallback(desc_strategies)
                
                if not title:
                    logger.debug(f"Skipped {item_id}: no title found")
                    return None
                
                result = {
                    "item_id": item_id,
                    "title": title,
                    "description": description,
                    "url": url,
                    "scraped_at": datetime.now().isoformat()
                }
                
                logger.info(f"Scraped: {title} (ID: {item_id})")
                return result
                
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1} failed for {item_id}: {e}")
                if attempt < self.max_retries - 1:
                    self.jittered_delay(3 * (2 ** attempt))  # 3s, 6s, 12s
        
        logger.error(f"Failed to scrape {item_id} after {self.max_retries} attempts")
        return None
    
    def run(self, items):
        """Main execution loop."""
        try:
            self.init_driver()
            
            for item_id in items:
                if len(self.results) >= config.TARGET_COUNT:
                    logger.info(f"Reached target count ({config.TARGET_COUNT})")
                    break
                
                result = self.scrape_item(item_id)
                if result:
                    self.results.append(result)
                
                self.jittered_delay()
            
            self.save_results()
            logger.info(f"Complete. Scraped {len(self.results)} items.")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            self.save_results()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.save_results()
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Save results to JSON."""
        import os
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        with open(config.OUTPUT_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {config.OUTPUT_FILE}")


if __name__ == "__main__":
    # Example: scrape items 1-100
    items = [str(i) for i in range(1, 101)]
    
    scraper = WebScraper()
    scraper.run(items)
