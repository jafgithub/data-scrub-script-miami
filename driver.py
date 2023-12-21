import logging

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class CustomWebDriver(WebDriver):
    def __init__(
        self, headless=True, is_eager=False, disable_images=False, is_none=False
    ):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        options.add_argument("--lang=en")
        # options.add_argument(
        # )
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-extensions")
        # options.add_argument("--window-size=1280,1024")
        # options.add_argument("--log-level=3")
        # options.add_argument("--disable-notifications")
        # options.add_argument("--disable-gpu")

        ### Added experimental_options to hide "Chrome is being controlled by automated test software"
        # options.add_experimental_option("useAutomationExtension", False)
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # print(options)
        if headless:
            options.add_argument("--headless=new")
        if is_none:
            options.page_load_strategy = "none"
        if is_eager:
            options.page_load_strategy = "eager"
        if disable_images:
            options.add_argument("--blink-settings=imagesEnabled=false")

        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument('--no-sandbox')
        # print("GG")
        # options.add_argument('--user-data-dir=~/.config/google-chrome')
        options.add_argument("--disable-extensions")


        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        service = ChromeService(executable_path="/home/ubuntu/events-scrap/chromedriver-linux64/chromedriver")

        super().__init__(service=service, options=options)
        self.maximize_window()

    def wait_for(self, expected_condition, *ec_args, timeout=10):
        try:
            condition_function = getattr(EC, expected_condition, None)
            if condition_function:
                try:
                    element = WebDriverWait(self, timeout).until(
                        condition_function(*ec_args)
                    )
                except Exception:
                    element = WebDriverWait(self, timeout).until(
                        condition_function(ec_args)
                    )
                return element
        except Exception:
            logging.exception(f"Element not found:")
            return None


## example usage
# if __name__ == "__main__":
#     # try:
#     #     # Initialize the custom WebDriver
#         custom_driver = CustomWebDriver(disable_images=True)

#         # Navigate to a website
#         custom_driver.get("https://example.com")

#         # Wait for an element to be present and interact with it
#         search_input = custom_driver.wait_for_element(By.NAME, "q", 10)
#         custom_driver.quit()
