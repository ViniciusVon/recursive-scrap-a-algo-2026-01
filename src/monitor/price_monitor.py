"""
Price Monitor Module

Monitors a price element on a webpage using Selenium and RegEx.
Detects changes and logs the XPath/position of the element.

Big O Analysis:
- find_price_element(): O(n) where n is the number of elements in the page
- extract_price_value(): O(m) where m is the length of the text content
- monitor(): O(k * n) where k is the number of monitoring cycles
"""

import re
import time
from typing import Optional, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class PriceMonitor:
    """
    Monitors price changes on a webpage.

    Attributes:
        url (str): The URL to monitor
        driver (webdriver.Chrome): Selenium WebDriver instance
        current_price (float): The current tracked price
        price_pattern (re.Pattern): RegEx pattern for price extraction
    """

    # RegEx pattern to match common price formats (e.g., $1,234.56 or R$ 1.234,56)
    DEFAULT_PRICE_PATTERN = r'[\$R\€\£]?\s*[\d.,]+(?:[.,]\d{2})?'

    def __init__(self, url: str, price_pattern: Optional[str] = None, headless: bool = True):
        """
        Initialize the PriceMonitor.

        Args:
            url: The webpage URL to monitor
            price_pattern: Custom RegEx pattern for price matching (optional)
            headless: Run browser in headless mode (default: True)

        Time Complexity: O(1)
        """
        self.url = url
        self.price_pattern = re.compile(price_pattern or self.DEFAULT_PRICE_PATTERN)
        self.current_price: Optional[float] = None
        self.price_element_xpath: Optional[str] = None
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless

    def start_driver(self) -> None:
        """
        Initialize the Selenium WebDriver.

        Time Complexity: O(1)
        """
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        print(f"[MONITOR] WebDriver initialized")

    def stop_driver(self) -> None:
        """
        Close the Selenium WebDriver.

        Time Complexity: O(1)
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
            print(f"[MONITOR] WebDriver closed")

    def load_page(self) -> None:
        """
        Load the target webpage.

        Time Complexity: O(1) - network dependent
        """
        if not self.driver:
            self.start_driver()
        self.driver.get(self.url)
        print(f"[MONITOR] Page loaded: {self.url}")

    def find_price_elements(self) -> list[WebElement]:
        """
        Find all elements containing price-like values.

        Returns:
            List of WebElements containing prices

        Time Complexity: O(n) where n is the number of elements in the DOM
        """
        # Get all text-containing elements - O(n)
        all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")

        price_elements = []
        # Iterate through elements - O(n)
        for element in all_elements:
            try:
                text = element.text
                # Check if text matches price pattern - O(m) where m is text length
                if self.price_pattern.search(text):
                    price_elements.append(element)
            except Exception:
                continue

        print(f"[MONITOR] Found {len(price_elements)} potential price elements")
        return price_elements

    def get_element_xpath(self, element: WebElement) -> str:
        """
        Generate the XPath for a given element.

        Args:
            element: The WebElement to get XPath for

        Returns:
            XPath string for the element

        Time Complexity: O(d) where d is the depth of the element in DOM
        """
        # Use JavaScript to generate XPath - O(d)
        script = """
        function getXPath(element) {
            if (element.id !== '')
                return '//*[@id="' + element.id + '"]';
            if (element === document.body)
                return '/html/body';

            var ix = 0;
            var siblings = element.parentNode.childNodes;
            for (var i = 0; i < siblings.length; i++) {
                var sibling = siblings[i];
                if (sibling === element)
                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                    ix++;
            }
        }
        return getXPath(arguments[0]);
        """
        xpath = self.driver.execute_script(script, element)
        return xpath

    def extract_price_value(self, text: str) -> Optional[float]:
        """
        Extract numeric price value from text.

        Args:
            text: Text containing a price

        Returns:
            Float price value or None if not found

        Time Complexity: O(m) where m is the length of the text
        """
        match = self.price_pattern.search(text)
        if not match:
            return None

        price_str = match.group()
        # Remove currency symbols and spaces - O(m)
        price_str = re.sub(r'[^\d.,]', '', price_str)

        # Handle different decimal formats (1,234.56 vs 1.234,56)
        if ',' in price_str and '.' in price_str:
            if price_str.rfind(',') > price_str.rfind('.'):
                # European format: 1.234,56
                price_str = price_str.replace('.', '').replace(',', '.')
            else:
                # US format: 1,234.56
                price_str = price_str.replace(',', '')
        elif ',' in price_str:
            # Could be 1,234 or 1,23 - assume comma is decimal if 2 digits after
            parts = price_str.split(',')
            if len(parts[-1]) == 2:
                price_str = price_str.replace(',', '.')
            else:
                price_str = price_str.replace(',', '')

        try:
            return float(price_str)
        except ValueError:
            return None

    def select_price_element(self, elements: list[WebElement], user_index: Optional[int] = None) -> Optional[WebElement]:
        """
        Allow user to select which element contains the target price.

        Args:
            elements: List of price elements found
            user_index: Pre-selected index (optional, for automation)

        Returns:
            Selected WebElement or None

        Time Complexity: O(n) where n is number of elements
        """
        if not elements:
            print("[MONITOR] No price elements found")
            return None

        print("\n[MONITOR] Found the following price elements:")
        for i, elem in enumerate(elements):
            xpath = self.get_element_xpath(elem)
            print(f"  [{i}] Value: {elem.text} | XPath: {xpath}")

        if user_index is not None:
            if 0 <= user_index < len(elements):
                selected = elements[user_index]
                self.price_element_xpath = self.get_element_xpath(selected)
                print(f"\n[MONITOR] Auto-selected element [{user_index}]")
                print(f"[MONITOR] XPath: {self.price_element_xpath}")
                return selected
            else:
                print(f"[MONITOR] Invalid index: {user_index}")
                return None

        while True:
            try:
                choice = input("\nSelect the price element index to monitor (or 'q' to quit): ")
                if choice.lower() == 'q':
                    return None
                index = int(choice)
                if 0 <= index < len(elements):
                    selected = elements[index]
                    self.price_element_xpath = self.get_element_xpath(selected)
                    print(f"[MONITOR] Selected element XPath: {self.price_element_xpath}")
                    return selected
                else:
                    print(f"[MONITOR] Invalid index. Choose 0-{len(elements)-1}")
            except ValueError:
                print("[MONITOR] Please enter a valid number")

    def get_current_price(self) -> Optional[float]:
        """
        Get the current price from the monitored element.

        Returns:
            Current price as float or None

        Time Complexity: O(m) where m is text length
        """
        if not self.price_element_xpath:
            print("[MONITOR] No element selected for monitoring")
            return None

        try:
            element = self.driver.find_element(By.XPATH, self.price_element_xpath)
            return self.extract_price_value(element.text)
        except Exception as e:
            print(f"[MONITOR] Error getting price: {e}")
            return None

    def monitor(self, interval: float = 5.0, on_change: Optional[Callable[[float, float], None]] = None) -> None:
        """
        Start monitoring for price changes.

        Args:
            interval: Time between checks in seconds
            on_change: Callback function when price changes (old_price, new_price)

        Time Complexity: O(k * m) where k is number of cycles, m is text length
        """
        print(f"\n[MONITOR] Starting price monitoring (interval: {interval}s)")
        print("[MONITOR] Press Ctrl+C to stop\n")

        self.current_price = self.get_current_price()
        print(f"[MONITOR] Initial price: {self.current_price}")

        try:
            while True:
                time.sleep(interval)
                self.driver.refresh()

                new_price = self.get_current_price()

                if new_price is None:
                    print("[MONITOR] Could not read price, retrying...")
                    continue

                if new_price != self.current_price:
                    old_price = self.current_price
                    self.current_price = new_price
                    print(f"[MONITOR] PRICE CHANGED: {old_price} -> {new_price}")

                    if on_change:
                        on_change(old_price, new_price)
                else:
                    print(f"[MONITOR] Price unchanged: {new_price}")

        except KeyboardInterrupt:
            print("\n[MONITOR] Monitoring stopped by user")
