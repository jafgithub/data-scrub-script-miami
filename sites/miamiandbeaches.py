import logging
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from driver import CustomWebDriver
from event import Event
# from utils import save_and_upload_image


def fetch_events_from_miami_and_beaches(days=1, **kwargs):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Origin": "https://www.miamiandbeaches.com",
        "Referer": "https://www.miamiandbeaches.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded",
        "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    url = "https://y72zzu5ph1-1.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.17.1)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.55.0)%3B%20Vue%20(3.2.47)%3B%20Vue%20InstantSearch%20(4.9.0)%3B%20JS%20Helper%20(3.13.0)&x-algolia-api-key=08bbc181e65b799cb34162e4de5bb3fb&x-algolia-application-id=Y72ZZU5PH1"

    start_time = datetime.now()
    end_time = start_time + timedelta(days=days)
    logging.info(f"Start Time: {start_time}, End Time: {end_time}")

    data = {
        "requests": [
            {
                "indexName": "prd-item",
                "params": f"aroundLatLng=&aroundRadius=all&facets=%5B%22region%22%2C%22categories%22%2C%22subcategories%22%2C%22eventTypes%22%5D&filters=_datesFilter%3A{int(start_time.timestamp())}%20TO%20{int(end_time.timestamp())}%20AND%20(type%3Aevent)&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=1000&maxValuesPerFacet=200&page=&query=Miami&tagFilters=",
            }
        ]
    }

    logging.info(f"Request Params: {data['requests'][0]['params']}")
    events = []

    try:
        results = []
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        response = response.json()
        response = response.get("results", [])[0].get("hits", [])
        logging.info(f"Events found: {len(response)}")
        logging.info(f"Number of events: {len(response)}")
        for i, record in enumerate(response):
            start_time = datetime.fromtimestamp(
                int(
                    record["_datesFilter"][0]
                    if len(record["_datesFilter"]) > 1
                    else record["_datesFilter"][0]
                )
            )
            end_time = datetime.fromtimestamp(
                int(
                    record["_datesFilter"][-1]
                    if len(record["_datesFilter"]) > 1
                    else record["_datesFilter"][0]
                )
            )

            try:
                an_event = Event()

                an_event["title"] = record["name"]
                an_event["sdate"] = start_time.date()
                an_event["stime"] = start_time.time()
                an_event["etime"] = end_time.time()
                description = record["description"]
                if description:
                    description = BeautifulSoup(description, "html.parser").get_text()
                else:
                    description = "NONE"
                an_event["description"] = description
                an_event["disclaimer"] = "NONE"
                an_event["latitude"] = (
                    record["_geoloc"]["lat"] if "_geoloc" in record else ""
                )
                an_event["longitude"] = (
                    record["_geoloc"]["lng"]
                    if "_geoloc" in record
                    else record["_geoloc"]["long"]
                    if "_geoloc" in record
                    else ""
                )
                an_event["place_name"] = record["region"]
                an_event["event category"] = ", ".join(record["categories"]).lstrip(
                    ", "
                )
                an_event[
                    "event_url"
                ] = f'https://www.miamiandbeaches.com{record["pageUrl"]}'
                an_event["edate"] = end_time.date()

                results.append(an_event)

                logging.info(
                    f"Event {i} processed successfully. {an_event['event_url']}"
                )
            except KeyError:
                logging.exception(
                    f"KeyError: occurred while processing Event {i}. url = {an_event['event_url']}"
                )
    except requests.exceptions.RequestException:
        logging.exception(f"Request Exception: occurred.")
    except ValueError:
        logging.exception(f"ValueError: occurred while processing the response JSON.")
    except Exception:
        logging.exception(f"An error occurred: ")

    # events = prepare_data_for_excel(events)
    driver = CustomWebDriver(is_eager=True)
    # print(events)
    results = scrap_address_and_image(driver=driver, events=results)
    return results


def scrap_address_and_image(driver: CustomWebDriver, events):
    logging.info("Getting events images...")
    for i, event in enumerate(events):
        event_url = event["event_url"]  # getting event URL
        driver.get(event_url)
        try:
            image_div: WebElement = driver.wait_for(
                "visibility_of_element_located",
                By.CLASS_NAME,
                "ys-event-details__hero-section__image",
                timeout=12,
            )
            # image_div = driver.find_element(By.CLASS_NAME, 'ys-event-details__hero-section__image')
            style_attribute = image_div.get_attribute("style")
            # print(style_attribute)
            url_match = re.search(r"url\((.*?)\)", style_attribute)
            # print(url_match)
            if url_match:
                image_url = url_match.group(1).strip('"')
                # print(image_url)

                if image_url.startswith("/getmedia/"):
                    image_url = f"https://www.miamiandbeaches.com{image_url}"
                else:
                    image_url = image_url
                logging.info(f"Background Image URL: {image_url}")
                # if image_url:
                #     pass
                #     # image_url = save_and_upload_image(
                #     #     url=image_url, website_name="miamiandbeaches.com"
                #     # )
                #     # if image_url == "NONE":
                #     #     file_name = "NONE"
                #     # else:
                #     #     file_name, image_url = image_url
                # else:
                #     image_url
            # change index here
            # events[i]["img"] = f"images/event/{file_name}"  # data:image_url
            # events[i]["cover_img"] = f"images/event/{file_name}"  # data:image_url
            try:
                events[i]["original_img_name"] = image_url  # data:original_img_name
            except:
                logging.info(f'fetching image for {i} event')
                image_element = driver.find_element(By.TAG_NAME, 'img')
                image_source = image_element.get_attribute('src')
                events[i]["original_img_name"] = image_source

        except Exception:
            logging.exception(
                f"An unexpected error occurred while scraping event image for {event_url}"
            , exc_info=True)
            # Raise the error to propagate it further
            raise
            # continue

        try:
            address_div: WebElement = driver.wait_for(
                "presence_of_element_located", By.CLASS_NAME, "contact-info", timeout=12
            )
            # address_div = driver.find_element(By.CLASS_NAME, "contact-info")
            address_anchor = address_div.find_element(By.TAG_NAME, "a")
            address_url = address_anchor.get_attribute("href")
            address = address_anchor.text

            # CHANGE INDEX
            events[i]["address"] = address  # data:full_address
            events[i]["address_url"] = address_url  # data:address_url

        except BaseException:
            logging.exception(
                f"An unexpected error occurred while scraping event address for {event_url}"
            , exc_info=True)
            raise
    return events


if __name__ == "__main__":
    fetch_events_from_miami_and_beaches()
