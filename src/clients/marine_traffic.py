"""
Marine Traffic client using undetected-chromedriver to bypass Cloudflare.
"""

import logging
import time
from datetime import datetime
from typing import Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config import Config
from src.models.signage_data import MarineTrafficData

logger = logging.getLogger(__name__)


class MarineTrafficClient:
    """
    Client for Marine Traffic using Selenium with undetected-chromedriver.
    Bypasses Cloudflare protection.
    """

    def __init__(self):
        """Initialize client with config."""
        self.url = Config.MARINE_TRAFFIC_URL
        self.username = Config.MARINE_TRAFFIC_USERNAME
        self.password = Config.MARINE_TRAFFIC_PASSWORD
        self.screenshot_dir = Config.CACHE_PATH / "marine_screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        if not self.url:
            logger.warning("MARINE_TRAFFIC_URL not configured")

    def capture_map(self) -> Optional[MarineTrafficData]:
        """
        Capture marine traffic map screenshot using undetected Chrome.

        Returns:
            MarineTrafficData with screenshot path or None on failure
        """
        if not self.url:
            logger.debug("Marine traffic not configured, skipping")
            return None

        driver = None
        try:
            # Configure Chrome options for 4K resolution
            options = uc.ChromeOptions()
            # options.add_argument('--headless=new')  # Disabled to bypass Cloudflare
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")

            # Launch undetected Chrome
            logger.info("Launching browser...")
            driver = uc.Chrome(options=options, version_main=None)

            # Set window size and viewport to exact 4K dimensions
            driver.set_window_size(Config.IMAGE_WIDTH, Config.IMAGE_HEIGHT)
            driver.execute_script(f"window.resizeTo({Config.IMAGE_WIDTH}, {Config.IMAGE_HEIGHT});")
            driver.execute_cdp_cmd(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": Config.IMAGE_WIDTH,
                    "height": Config.IMAGE_HEIGHT,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                },
            )

            # Navigate to marine traffic
            logger.info(f"Navigating to {self.url}")
            driver.get(self.url)

            # Wait for Cloudflare check to complete
            logger.info("Waiting for page to load...")
            time.sleep(15)  # Give Cloudflare time to check

            # Dismiss privacy popup - try multiple strategies
            try:
                # Wait for and click the privacy consent button
                wait = WebDriverWait(driver, 10)

                # Try common privacy popup selectors
                selectors = [
                    "button[class*='agree']",
                    "button[class*='accept']",
                    "button[class*='consent']",
                    "a[class*='agree']",
                    "a[class*='accept']",
                    "//button[contains(translate(., 'AGREE', 'agree'), 'agree')]",
                    "//button[contains(translate(., 'ACCEPT', 'accept'), 'accept')]",
                    "//a[contains(translate(., 'AGREE', 'agree'), 'agree')]",
                ]

                clicked = False
                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        else:
                            element = wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        element.click()
                        logger.info(f"Clicked privacy button with selector: {selector}")
                        clicked = True
                        time.sleep(2)
                        break
                    except:
                        continue

                # Fallback: try text-based button finding
                if not clicked:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        try:
                            text = button.text.lower()
                            if any(
                                word in text
                                for word in ["agree", "accept", "ok", "got it", "i agree"]
                            ):
                                button.click()
                                logger.info(f"Dismissed privacy popup: {button.text}")
                                time.sleep(2)
                                break
                        except:
                            continue
            except Exception as e:
                logger.debug(f"Privacy popup handling: {e}")

            # Check if we got past Cloudflare
            if "blocked" in driver.page_source.lower() or "cloudflare" in driver.title.lower():
                logger.error("Still blocked by Cloudflare")
                return None

            # Wait for map to load
            logger.info("Waiting for map...")
            time.sleep(5)

            # Generate screenshot filename
            timestamp = datetime.now()
            filename = f"marine_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = self.screenshot_dir / filename

            # Capture screenshot
            driver.save_screenshot(str(screenshot_path))
            logger.info(f"Captured screenshot: {screenshot_path}")

            # Try to count vessels
            vessel_count = 0

            return MarineTrafficData(
                screenshot_path=screenshot_path, vessel_count=vessel_count, timestamp=timestamp
            )

        except Exception as e:
            logger.error(f"Failed to capture marine traffic screenshot: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None

        finally:
            if driver:
                driver.quit()
