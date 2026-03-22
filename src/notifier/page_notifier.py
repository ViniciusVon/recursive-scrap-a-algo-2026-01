"""
Page Notifier Module

Interacts with a public webpage to send notifications about price changes.
Uses Selenium to fill forms and click buttons.

Big O Analysis:
- navigate_to_page(): O(1) - network dependent
- find_text_input(): O(n) where n is the number of elements
- find_button(): O(n) where n is the number of elements
- send_notification(): O(n) total for finding and interacting with elements
"""

import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class PageNotifier:
    """
    Sends notifications via a public webpage.

    Attributes:
        url (str): The notification page URL
        driver (webdriver.Chrome): Selenium WebDriver instance
        text_input_xpath (str): XPath to the text input field
        button_xpath (str): XPath to the submit button
    """

    def __init__(self, url: str, headless: bool = False):
        """
        Initialize the PageNotifier.

        Args:
            url: The notification page URL
            headless: Run browser in headless mode (default: False for visibility)

        Time Complexity: O(1)
        """
        self.url = url
        self.driver: Optional[webdriver.Chrome] = None
        self.text_input_xpath: Optional[str] = None
        self.button_xpath: Optional[str] = None
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
        print(f"[NOTIFIER] WebDriver initialized")

    def stop_driver(self) -> None:
        """
        Close the Selenium WebDriver.

        Time Complexity: O(1)
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
            print(f"[NOTIFIER] WebDriver closed")

    def navigate_to_page(self) -> None:
        """
        Navigate to the notification page.

        Time Complexity: O(1) - network dependent
        """
        if not self.driver:
            self.start_driver()
        self.driver.get(self.url)
        print(f"[NOTIFIER] Navigated to: {self.url}")

    def get_element_xpath(self, element: WebElement) -> str:
        """
        Generate the XPath for a given element.

        Args:
            element: The WebElement to get XPath for

        Returns:
            XPath string for the element

        Time Complexity: O(d) where d is the depth of the element in DOM
        """
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
        return self.driver.execute_script(script, element)

    def find_text_inputs(self) -> list[WebElement]:
        """
        Find all text input fields on the page.

        Returns:
            List of text input WebElements

        Time Complexity: O(n) where n is the number of elements
        """
        inputs = []

        # Find input elements - O(n)
        input_elements = self.driver.find_elements(
            By.XPATH,
            "//input[@type='text' or @type='email' or not(@type)] | //textarea"
        )

        for elem in input_elements:
            if elem.is_displayed() and elem.is_enabled():
                inputs.append(elem)

        print(f"[NOTIFIER] Found {len(inputs)} text input fields")
        return inputs

    def find_buttons(self) -> list[WebElement]:
        """
        Find all clickable buttons on the page.

        Returns:
            List of button WebElements

        Time Complexity: O(n) where n is the number of elements
        """
        buttons = []

        # Find button elements - O(n)
        button_elements = self.driver.find_elements(
            By.XPATH,
            "//button | //input[@type='submit'] | //input[@type='button'] | //*[@role='button']"
        )

        for elem in button_elements:
            if elem.is_displayed() and elem.is_enabled():
                buttons.append(elem)

        print(f"[NOTIFIER] Found {len(buttons)} buttons")
        return buttons

    def select_text_input(self, inputs: list[WebElement], user_index: Optional[int] = None) -> Optional[WebElement]:
        """
        Allow user to select which text input to use.

        Args:
            inputs: List of text input elements
            user_index: Pre-selected index (optional)

        Returns:
            Selected WebElement or None

        Time Complexity: O(n) where n is number of inputs
        """
        if not inputs:
            print("[NOTIFIER] No text inputs found")
            return None

        print("\n[NOTIFIER] Found the following text inputs:")
        for i, elem in enumerate(inputs):
            xpath = self.get_element_xpath(elem)
            placeholder = elem.get_attribute('placeholder') or elem.get_attribute('name') or 'N/A'
            print(f"  [{i}] Placeholder/Name: {placeholder} | XPath: {xpath}")

        if user_index is not None:
            if 0 <= user_index < len(inputs):
                selected = inputs[user_index]
                self.text_input_xpath = self.get_element_xpath(selected)
                print(f"\n[NOTIFIER] Auto-selected input [{user_index}]")
                return selected
            else:
                print(f"[NOTIFIER] Invalid index: {user_index}")
                return None

        while True:
            try:
                choice = input("\nSelect the text input index to use (or 'q' to quit): ")
                if choice.lower() == 'q':
                    return None
                index = int(choice)
                if 0 <= index < len(inputs):
                    selected = inputs[index]
                    self.text_input_xpath = self.get_element_xpath(selected)
                    print(f"[NOTIFIER] Selected input XPath: {self.text_input_xpath}")
                    return selected
                else:
                    print(f"[NOTIFIER] Invalid index. Choose 0-{len(inputs)-1}")
            except ValueError:
                print("[NOTIFIER] Please enter a valid number")

    def select_button(self, buttons: list[WebElement], user_index: Optional[int] = None) -> Optional[WebElement]:
        """
        Allow user to select which button to click.

        Args:
            buttons: List of button elements
            user_index: Pre-selected index (optional)

        Returns:
            Selected WebElement or None

        Time Complexity: O(n) where n is number of buttons
        """
        if not buttons:
            print("[NOTIFIER] No buttons found")
            return None

        print("\n[NOTIFIER] Found the following buttons:")
        for i, elem in enumerate(buttons):
            xpath = self.get_element_xpath(elem)
            text = elem.text or elem.get_attribute('value') or 'N/A'
            print(f"  [{i}] Text: {text} | XPath: {xpath}")

        if user_index is not None:
            if 0 <= user_index < len(buttons):
                selected = buttons[user_index]
                self.button_xpath = self.get_element_xpath(selected)
                print(f"\n[NOTIFIER] Auto-selected button [{user_index}]")
                return selected
            else:
                print(f"[NOTIFIER] Invalid index: {user_index}")
                return None

        while True:
            try:
                choice = input("\nSelect the button index to click (or 'q' to quit): ")
                if choice.lower() == 'q':
                    return None
                index = int(choice)
                if 0 <= index < len(buttons):
                    selected = buttons[index]
                    self.button_xpath = self.get_element_xpath(selected)
                    print(f"[NOTIFIER] Selected button XPath: {self.button_xpath}")
                    return selected
                else:
                    print(f"[NOTIFIER] Invalid index. Choose 0-{len(buttons)-1}")
            except ValueError:
                print("[NOTIFIER] Please enter a valid number")

    def send_notification(self, old_price: float, new_price: float) -> bool:
        """
        Send a notification about price change.

        Args:
            old_price: The previous price
            new_price: The new price

        Returns:
            True if notification sent successfully

        Time Complexity: O(1) - uses pre-stored XPaths
        """
        if not self.text_input_xpath or not self.button_xpath:
            print("[NOTIFIER] Text input or button not configured")
            return False

        try:
            # Navigate to page if needed
            self.navigate_to_page()
            time.sleep(1)  # Wait for page load

            # Find and fill text input - O(1) with XPath
            text_input = self.driver.find_element(By.XPATH, self.text_input_xpath)
            message = f"Price Alert! Old: {old_price} -> New: {new_price}"
            text_input.clear()
            text_input.send_keys(message)
            print(f"[NOTIFIER] Entered message: {message}")

            # Find and click button - O(1) with XPath
            button = self.driver.find_element(By.XPATH, self.button_xpath)
            button.click()
            print(f"[NOTIFIER] Clicked submit button")

            return True

        except Exception as e:
            print(f"[NOTIFIER] Error sending notification: {e}")
            return False

    def setup_interactive(self) -> bool:
        """
        Interactive setup for selecting text input and button.

        Returns:
            True if setup completed successfully

        Time Complexity: O(n) where n is number of elements
        """
        self.navigate_to_page()
        time.sleep(2)  # Wait for page to fully load

        # Select text input
        inputs = self.find_text_inputs()
        if not self.select_text_input(inputs):
            return False

        # Select button
        buttons = self.find_buttons()
        if not self.select_button(buttons):
            return False

        print("\n[NOTIFIER] Setup complete!")
        return True
