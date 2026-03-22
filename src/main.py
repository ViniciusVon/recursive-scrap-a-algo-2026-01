"""
Auction Bid Assistant - Main Entry Point

A system to monitor prices on auction websites and send notifications
when prices change.

Big O Analysis Summary:
- Overall monitoring loop: O(k * n) where k is cycles, n is DOM elements
- Price extraction: O(m) where m is text length
- Notification: O(n) for element finding, O(1) for interaction
- Logging: O(1) per action, O(n) for summary

Total Space Complexity: O(n + m + l)
- n: number of tracked elements
- m: size of page content
- l: number of log entries
"""

import sys
from typing import Optional

from src.monitor import PriceMonitor
from src.notifier import PageNotifier
from src.logger import ActionLogger
from src.utils import validate_url


class AuctionBidAssistant:
    """
    Main application class for the Auction Bid Assistant.

    Coordinates the price monitor, notifier, and action logger.
    """

    def __init__(self):
        """Initialize the assistant."""
        self.logger = ActionLogger()
        self.monitor: Optional[PriceMonitor] = None
        self.notifier: Optional[PageNotifier] = None

    def setup(self) -> bool:
        """
        Interactive setup for the assistant.

        Returns:
            True if setup completed successfully
        """
        print("\n" + "="*60)
        print("  AUCTION BID ASSISTANT")
        print("  Monitor prices and get notified on changes")
        print("="*60 + "\n")

        # Request username
        if not self.logger.request_username():
            print("\n[ERROR] Username is required to continue")
            return False

        # Get monitor URL
        print("\n[SETUP] Enter the URL of the page to monitor:")
        monitor_url = input("Monitor URL: ").strip()

        is_valid, error = validate_url(monitor_url)
        if not is_valid:
            print(f"[ERROR] {error}")
            self.logger.log_action("ERROR", f"Invalid monitor URL: {error}")
            return False

        self.logger.log_action("CONFIG", f"Monitor URL set: {monitor_url}")

        # Get notification URL
        print("\n[SETUP] Enter the URL of the notification page (e.g., Gmail compose):")
        notifier_url = input("Notifier URL: ").strip()

        is_valid, error = validate_url(notifier_url)
        if not is_valid:
            print(f"[ERROR] {error}")
            self.logger.log_action("ERROR", f"Invalid notifier URL: {error}")
            return False

        self.logger.log_action("CONFIG", f"Notifier URL set: {notifier_url}")

        # Initialize components
        self.monitor = PriceMonitor(monitor_url, headless=False)
        self.notifier = PageNotifier(notifier_url, headless=False)

        return True

    def configure_monitor(self) -> bool:
        """
        Configure the price monitor by selecting the element to track.

        Returns:
            True if configuration successful
        """
        print("\n[SETUP] Configuring price monitor...")
        self.logger.log_action("CONFIG", "Starting monitor configuration")

        try:
            self.monitor.load_page()
            elements = self.monitor.find_price_elements()

            if not elements:
                print("[ERROR] No price elements found on the page")
                self.logger.log_action("ERROR", "No price elements found")
                return False

            selected = self.monitor.select_price_element(elements)
            if not selected:
                self.logger.log_action("ERROR", "No element selected")
                return False

            self.logger.log_action("CONFIG", f"Price element selected: {self.monitor.price_element_xpath}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to configure monitor: {e}")
            self.logger.log_action("ERROR", f"Monitor configuration failed: {e}")
            return False

    def configure_notifier(self) -> bool:
        """
        Configure the notifier by selecting text input and button.

        Returns:
            True if configuration successful
        """
        print("\n[SETUP] Configuring notifier...")
        self.logger.log_action("CONFIG", "Starting notifier configuration")

        try:
            if self.notifier.setup_interactive():
                self.logger.log_action("CONFIG", f"Notifier configured - Input: {self.notifier.text_input_xpath}, Button: {self.notifier.button_xpath}")
                return True
            else:
                self.logger.log_action("ERROR", "Notifier configuration cancelled")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to configure notifier: {e}")
            self.logger.log_action("ERROR", f"Notifier configuration failed: {e}")
            return False

    def on_price_change(self, old_price: float, new_price: float) -> None:
        """
        Callback when price changes.

        Args:
            old_price: The previous price
            new_price: The new price
        """
        self.logger.log_action("PRICE_CHANGE", f"Price changed from {old_price} to {new_price}")

        print(f"\n[ALERT] Price changed: {old_price} -> {new_price}")
        print("[ALERT] Sending notification...")

        if self.notifier.send_notification(old_price, new_price):
            self.logger.log_action("NOTIFICATION", f"Notification sent successfully")
        else:
            self.logger.log_action("ERROR", "Failed to send notification")

    def start_monitoring(self, interval: float = 5.0) -> None:
        """
        Start the price monitoring loop.

        Args:
            interval: Time between checks in seconds
        """
        self.logger.log_action("MONITOR_START", f"Starting monitoring with {interval}s interval")

        try:
            self.monitor.monitor(interval=interval, on_change=self.on_price_change)
        except KeyboardInterrupt:
            self.logger.log_action("MONITOR_STOP", "Monitoring stopped by user")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources."""
        print("\n[CLEANUP] Shutting down...")

        if self.monitor:
            self.monitor.stop_driver()
        if self.notifier:
            self.notifier.stop_driver()

        # Print log summary
        print(self.logger.get_logs_summary())
        self.logger.log_action("SHUTDOWN", "Application closed")

    def run(self) -> None:
        """Main application entry point."""
        try:
            if not self.setup():
                return

            if not self.configure_monitor():
                self.cleanup()
                return

            if not self.configure_notifier():
                self.cleanup()
                return

            # Get monitoring interval
            print("\n[SETUP] Enter monitoring interval in seconds (default: 5):")
            interval_str = input("Interval: ").strip()

            try:
                interval = float(interval_str) if interval_str else 5.0
            except ValueError:
                interval = 5.0

            self.logger.log_action("CONFIG", f"Monitoring interval set to {interval}s")

            # Start monitoring
            self.start_monitoring(interval)

        except Exception as e:
            print(f"\n[FATAL ERROR] {e}")
            self.logger.log_action("FATAL_ERROR", str(e))
            self.cleanup()


def main():
    """Application entry point."""
    assistant = AuctionBidAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
