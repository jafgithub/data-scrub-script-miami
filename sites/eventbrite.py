import json
import time
import logging
from datetime import datetime, timedelta

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from event import Event
from driver import CustomWebDriver



def get_api_params(driver: CustomWebDriver, city: str = "Miami", days: int = 30):
    try:
        print('city is', city)
        driver.get(f"https://www.eventbrite.com/d/miami/all-events/?page=1")
        print('driver is-------------------', driver)
        driver.wait_for(
            "visibility_of_element_located", "xpath", "//input[@id='locationPicker']"
        )
        # WebDriverWait(driver, 10).until(
        #     EC.visibility_of_element_located((By.XPATH, ))
        # )
        location_input = driver.find_element(By.XPATH, "//input[@id='locationPicker']")
        location_input.click()
        location_input.clear()
        location_input.send_keys(city)
        time.sleep(1)
        location_input.send_keys(Keys.ENTER)
        body_element = driver.find_element(By.TAG_NAME, "body")
        body_element.click()
        time.sleep(10)
        history_value = driver.execute_script(
            "return window.localStorage.getItem('location:autocomplete:history');"
        )
        # driver.quit()

        if history_value:
            history_value = json.loads(history_value.replace(";", ","))
            place_id = history_value.get("placeId")
            # return place_id
        else:
            logging.exception("Place ID not found in local storage.")
            return None

        csrf_token = get_csrf_token(driver.get_cookies())

        if place_id and csrf_token:
            return place_id, csrf_token
    except Exception:
        logging.exception(f"Error occurred while retrieving API Params.")
        return None


def get_place_id(driver):
    max_attempts = 5
    attempt = 0
    history_value = None

    while attempt < max_attempts:
        try:
            history_value = driver.execute_script(
                "return window.localStorage.getItem('location:autocomplete:history');"
            )
            if history_value:
                history_value = json.loads(history_value.replace(";", ","))
                place_id = history_value.get("placeId")
                return place_id
            else:
                time.sleep(2)
                attempt += 1
        except Exception:
            logging.exception(f"Error occurred while getting history value.")
            break


def get_csrf_token(cookies):
    try:
        csrf_token = None
        for cookie in cookies:
            if cookie["name"] == "csrftoken":
                csrf_token = cookie["value"]
                break
        if csrf_token:
            return csrf_token
        else:
            logging.exception("CSRF token not found in cookies.")
            return None
    except Exception:
        logging.exception(f"Error occurred while retrieving CSRF token.")
        return None


def scrape_event_data(place_id, csrf_token, dates):
    file = open('images.txt', 'w+')
    try:
        url = "https://www.eventbrite.com/api/v3/destination/search/"

        headers = {
            "authority": "www.eventbrite.com",
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://www.eventbrite.com",
            "referer": "https://www.eventbrite.com/d/ca--san-francisco/all-events/?page=4",
            "sec-ch-ua": "",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '""',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "x-csrftoken": csrf_token,
            "x-requested-with": "XMLHttpRequest",
            "cookie": f"csrftoken={csrf_token};",
        }

        data = {
            "event_search": {
                "dates": "current_future",
                "date_range": {"from": dates["start_date"], "to": dates["end_date"]},
                "dedup": True,
                "places": [place_id],
                "page": 1,
                "page_size": 50,
                "online_events_only": False,
                "include_promoted_events_for": {
                    "interface": "search",
                    "request_source": "web",
                },
            },
            "expand.destination_event": [
                "primary_venue",
                "image",
                "ticket_availability",
                "primary_organizer",
            ],
            "debug_experiment_overrides": {"search_exp_1": "D"},
        }

        results = []

        page_number = 1
        while True:
            data["event_search"]["page"] = page_number
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()

            event_results = response_json.get("events", {}).get("results", [])

            if not event_results:
                break
            else:
                for event in event_results:
                    try:
                        image_url = event.get("image", None)
                        
                        if image_url:
                            # image_url = event.get('image', None)
                            image_url = image_url["original"]["url"]
                            file.write((image_url + '\n'))
                            # image_url = save_and_upload_image(
                            #     image_url, website_name="eventbrite.com"
                            # )
                            # if image_url == "NONE":
                                # file_name = "NONE"
                            # else:
                                # file_name, image_url = image_url
                        else:
                            image_url = "NONE"
                        categories = [
                                tag["display_name"]
                                for tag in event["tags"]
                                if tag.get("prefix", "").startswith("Eventbrite")
                            ]
                        # categories = 
                        
                        start_date = event["start_date"]
                        if start_date > dates["end_date"]:
                            continue
                        end_date = event["end_date"]
                        start_time = event["start_time"]
                        end_time = event["end_time"]
                        place_name = event["primary_venue"]["name"]
                        full_address = event["primary_venue"]["address"][
                            "localized_address_display"
                        ]
                        latitude = float(event["primary_venue"]["address"]["latitude"])
                        longitude = float(
                            event["primary_venue"]["address"]["longitude"]
                        )
                        organizer_name = event["primary_organizer"]["name"]
                        event_summary = event["summary"]
                        event_name = event["name"]
                        event_url = event["url"]

                        is_soldout = event["ticket_availability"]["is_sold_out"]
                        is_free = event["ticket_availability"]["is_free"]
                        ticket_price = event["ticket_availability"].get(
                            "minimum_ticket_price", None
                        )
                        if ticket_price:
                            ticket_price = ticket_price.get("major_value", "NONE")
                        else:
                            ticket_price = "NONE"
                        # ticket_status = event['ticket_availability']['has_available_tickets']

                        an_event = Event()

                        an_event["title"] = event_name
                        # an_event["img"] = "images/event/{file_name}"
                        # an_event["cover_img"] = "images/event/{file_name}"
                        an_event["sdate"] = start_date
                        an_event["stime"] = start_time
                        an_event["etime"] = end_time
                        an_event["address"] = full_address
                        an_event["description"] = event_summary
                        an_event["disclaimer"] = "NONE"
                        an_event["latitude"] = latitude
                        an_event["longitude"] = longitude
                        an_event["place_name"] = place_name
                        an_event["event category"] = categories
                        an_event["price"] = ticket_price
                        an_event["is_soldout"] = is_soldout
                        an_event["is_free"] = is_free
                        an_event["organizer"] = organizer_name
                        an_event["event_url"] = event_url
                        an_event["edate"] = end_date
                        an_event["original_img_name"] = image_url

                        results.append(an_event)

                        logging.info(
                            f"Event processed successfully. {an_event['event_url']}"
                        )
                    except Exception:
                        logging.exception(
                            f"KeyError: occurred while processing Event. url = {an_event['event_url']}"
                        )
                        continue

            page_number += 1

        return results
    except Exception:
        logging.exception(f"Error occurred while scraping event data({event_url}.")
        return []


def fetch_events_from_eventbrite(city="Miami", days=1):
    try:
        driver = 'chromedriver-linux64'
        place_id, csrf_token = get_api_params(driver, city, days)
        driver.quit()

        dates = {
            "start_date": datetime.today().strftime("%Y-%m-%d"),
            "end_date": (datetime.today() + timedelta(days)).strftime("%Y-%m-%d"),
        }
        event_data = scrape_event_data(
            place_id=place_id, csrf_token=csrf_token, dates=dates
        )

        return event_data

    except Exception:
        logging.exception(f"Error occurred during event data scraping and processing.")


if __name__ == "__main__":
    fetch_events_from_eventbrite()
