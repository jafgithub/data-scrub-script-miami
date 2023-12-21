import logging
import re
import time
from datetime import datetime, timedelta

from parsel import Selector
from selenium.common.exceptions import WebDriverException

from driver import CustomWebDriver
from event import Event
from utils import preprocess_date_string, get_driver
from selenium.webdriver.common.by import By



def scroll_page(driver: CustomWebDriver, url):
    try:
        driver.get(url)
        # print(url)
        # print(driver.title)
        # print(driver.page_source)
        # user_agent = driver.execute_script('return navigator.userAgent;')
        # driver
        # print(user_agent)
        old_height = driver.execute_script(
            """
            function getHeight() {
                let a = document.querySelector('.UbEfxe').scrollHeight;
                return a
            }
            return getHeight();
        """
        )

        # print("sd", driver.execute_script(
        #     """
        #     return document.title;
        # """
        # ))

        while True:
            driver.execute_script(
                "document.querySelector('.UbEfxe').scrollTo(0, document.querySelector('.UbEfxe').scrollHeight);"
            )
            time.sleep(1)

            new_height = driver.execute_script(
                """
                function getHeight() {
                    return document.querySelector('.UbEfxe').scrollHeight;
                }
                return getHeight();
            """
            )

            if new_height == old_height:
                break

            old_height = new_height

        selector = Selector(driver.page_source)
        # driver.quit()

        return selector
    except WebDriverException as e:
        # Log the error
        logging.exception(f"Error occurred while scrolling the page: {e}")
        # Raise the error to propagate it further
        raise

    except Exception:
        # Log other unexpected exceptions
        logging.exception("An unexpected error occurred while scrolling the page")
        # Raise the error to propagate it further
        raise


def scrape_google_events(events_until_date, selector: Selector):
    try:
        results = []  # storing events
        logging.info(f"Events found: {len(selector.css('.scm-c'))}")
        for event in selector.css(".scm-c")[:]:
            try:
                an_event = Event()
                # eid = create_unique_object_id()
                event_title = event.css(".dEuIWb::text").get()
                date_start = f"{event.css('.FTUoSb::text').get()} {event.css('.omoMNe::text').get()}"
                date_start = preprocess_date_string(date_string=date_start)

                if date_start > events_until_date:
                    continue

                date_when = event.css(".Gkoz3::text").get()
                full_address = [
                    part.css("::text").get() for part in event.css(".ov85De span")
                ]
                full_address = filter(None, full_address)
                full_address = ", ".join(full_address)
                event_url = event.css(".zTH3xc::attr(href)").get()
                location_link = "https://www.google.com" + event.css(
                    ".ozQmAd::attr(data-url)"
                ).get("")
                image_url = file_name = "NONE"
                image_url = event.css(".YQ4gaf.wA1Bge::attr(src)").get("")
                if not image_url:
                    # pass
                    # image_url = save_and_upload_image(
                    #     image_url, website_name="googleevents"
                    # )
                    # if image_url == "NONE":
                        file_name = "NONE"
                    # else:
                    #     file_name, image_url = image_url

                # else:
                    # image_url = "NONE"
                description = event.css(".PVlUWc::text").get("")
                place_name = event.css(".RVclrc::text").get()
                venue_link = (
                    "https://www.google.com" + event.css(".pzNwRe a::attr(href)").get()
                    if event.css(".pzNwRe a::attr(href)").get()
                    else None
                )

                an_event["title"] = event_title
                # an_event["img"] = f"images/event/{file_name}"
                # an_event["cover_img"] = f"images/event/{file_name}"
                an_event["sdate"] = date_start
                an_event["stime"] = "NONE"
                an_event["etime"] = "NONE"
                an_event["address"] = (full_address,)
                an_event["description"] = description
                an_event["disclaimer"] = "NONE"
                an_event["place_name"] = place_name
                an_event["event category"] = "NONE"
                an_event["address_url"] = location_link
                an_event["event_url"] = event_url
                an_event["edate"] = date_when
                an_event["original_img_name"] = image_url

                results.append(an_event)  # appending the newly created event
                logging.info(
                    f"Event {an_event['id']} processed successfully. {an_event['event_url']}"
                )
            except KeyError:
                logging.exception(
                    f"KeyError: occurred while processing Event {an_event['id']}. url = {an_event['event_url']}"
                )

        return results
    except Exception:
        logging.exception("An unexpected error occurred while scraping Google events")
        # Raise the error to propagate it further
        raise


def scrap_geo_code(driver: CustomWebDriver, events: list):
    try:
        for i, event in enumerate(events):
            try:
                location_link = event["address_url"]
                driver.get(location_link)

                check_new_url = driver.wait_for(
                    "url_changes", location_link, timeout=30
                )

                if check_new_url:
                    new_url = driver.current_url

                    pattern = r"@([-+]?[0-9]*\.?[0-9]+),([-+]?[0-9]*\.?[0-9]+)"
                    match = re.search(pattern, new_url)

                    if match:
                        latitude = match.group(1)
                        longitude = match.group(2)
                        events[i]["latitude"] = latitude
                        events[i]["longitude"] = longitude
                        
                        print("good")
                        # print("Latitude:", latitude)
                        # print("Longitude:", longitude)
                    else:
                        print("Latitude and longitude not found in the URL.")
                else:
                    pass
            except Exception:
                logging.exception(
                    "An unexpected error occurred while scraping geocode data"
                )
                event["latitude"] = "NONE"
                event["longitude"] = "NONE"
                continue

        driver.quit()
        return events
    except Exception:
        logging.exception("An unexpected error occurred while scraping geocode data")

        # Raise the error to propagate it further
        # raise e


def fetch_events_from_google_events(city="San Fransisco", days=30):
    try:
        logging.info(f"Google events scraping started for {city}")

        params = {
            "q": f"Events in {city}",  # search query
            "ibp": "htl;events",  # Google Events page
            "hl": "en",  # language
            "gl": "us",  # country of the search
        }

        events_until_date = datetime.now() + timedelta(days=days)
        # print(events_until_date)
        URL = f"https://www.google.com/search?q={params['q']}&ibp={params['ibp']}&hl={params['hl']}&gl={params['gl']}l"

        driver = CustomWebDriver()
        # driver = get_driver()
        result = scroll_page(driver, URL)
        google_events = scrape_google_events(
            events_until_date=events_until_date, selector=result
        )
        # print(len(google_events))
        google_events_w_cords = scrap_geo_code(driver, google_events)

        logging.info(
            f"Google events scrapped successfully. Events scraped: {len(google_events_w_cords)}"
        )
        # Raise the error to propagate it further
        return google_events_w_cords
    except Exception:
        logging.exception("An unexpected error occurred in the main() function")
        # Raise the error to propagate it further
        raise


if __name__ == "__main__":
    fetch_events_from_google_events()