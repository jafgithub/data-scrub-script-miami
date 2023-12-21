import json
import logging
import time
from datetime import datetime, timedelta

import aiohttp
import asyncio

import requests
from bs4 import BeautifulSoup

from event import Event
from utils import create_unique_object_id,GoogleDriveUploader

logging.basicConfig(
    filename="event_fetch.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

url = "https://allevents.in/api/index.php/categorization/web/v1/list"
headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "Cookie": "a=a;",
    "Referer": "https://allevents.in/hollywood/all?ref=cityhome-popmenuf",
}


def fetch_events_from_allevents(days=1, city="Miami"):
    url = "https://allevents.in/api/index.php/categorization/web/v1/list"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": "a=a;",
        "Referer": "https://allevents.in/hollywood/all?ref=cityhome-popmenuf",
    }

    try:
        event_urls = []
        events = []

        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)

        logging.info(
            f"Fetching events from allevents.in for {city} for the next {days} days."
        )
        data = {
            "venue": 0,
            "page": 1,
            "rows": 1000,
            "tag_type": None,
            "sdate": start_date.timestamp(),
            "edate": end_date.timestamp(),
            "city": city,
            "keywords": 0,
            "category": ["all"],
            "formats": 0,
            "popular": True,
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        results = []
        if response.status_code == 200:
            data = response.json()
            data = data.get("item", [])
            logging.info(f"Fetched {len(data)} events from allevents.in.")

            for record in data:
                # print(record)
                event_urls.append(record["event_url"])
            logging.info(f"Events found: {len(data)}")

            descriptions = get_desc(event_urls)
            for i, record in enumerate(data):
                stime = datetime.fromtimestamp(int(record["start_time"]))
                etime = datetime.fromtimestamp(int(record["end_time"]))
                # f"{event['latitude']} {event['longitude']}"
                instance = []
                try:
                    eid = create_unique_object_id()
                    event_name = record["eventname_raw"]
                    event_url = record["event_url"]
                    venue = record["location"]
                    image_url = record.get("banner_url","NONE")
                    if not image_url:
                        # event_image = save_and_upload_image(
                        #     image_url, website_name="allevents.in"
                        # )

                        image_url = "NONE"

                        # if event_image == "NONE":
                        #     file_name = "NONE"
                        # else:
                        #     file_name, event_image = event_image
                    start_time = stime.time()
                    end_time = etime.time()
                    start_date = stime.date()
                    end_date = etime.date()
                    latitude = float(record["venue"]["latitude"])
                    longitude = float(record["venue"]["longitude"])
                    full_address = record["venue"]["full_address"]
                    description = descriptions[i]
                    # categories = record["categories"][0] if record["categories"] is not None else "No Categories Provided"
                    categories = record.get("categories") and record.get("categories")[0] or "No Categories Provided"
                    ticket_price = record["tickets"].get("min_ticket_price", 0)

                    an_event = Event()

                    an_event["title"] = event_name
                    # an_event["img"] = f"images/event/{file_name}"
                    # an_event["cover_img"] = f"images/event/{file_name}"
                    an_event["sdate"] = start_date
                    an_event["stime"] = start_time
                    an_event["etime"] = end_time
                    an_event["address"] = full_address
                    an_event["description"] = description
                    an_event["disclaimer"] = "NONE"
                    an_event["latitude"] = latitude
                    an_event["longitude"] = longitude
                    an_event["place_name"] = venue
                    an_event["event category"] = categories
                    an_event["price"] = ticket_price
                    an_event["event_url"] = event_url
                    an_event["edate"] = end_date
                    an_event["original_img_name"] = image_url
                    results.append(an_event)
                    logging.info(f"Event {i} processed successfully. {event_url}")
                except KeyError:
                    logging.exception(
                        f"KeyError: occurred while processing Event {i}. url = {event_url}"
                    )

            # events = prepare_data_for_excel(events)
            return results
        else:
            logging.exception(f"Request failed with status code {response.status_code}")
    except Exception:
        logging.exception(f"An error occurred while fetching events from allevents.in")


def get_desc(urls=None):
    if urls is None:
        logging.exception("URLs are not provided")
        raise ValueError("URLs are not provided")
    descriptions = []
    logging.info("Fetching event descriptions from allevents.in")
    for i, url in enumerate(urls):
        try:
            response = requests.get(url)
            html_content = response.content
            soup = BeautifulSoup(html_content, "html.parser")
            element = soup.find("div", class_="event-description-html")
            data = element.get_text(strip=True) if element is not None else ""
            descriptions.append(data)
        except Exception:
            logging.warning(
                f"An error occurred while fetching event description for URL {url}."
            )
            descriptions.append("")

    logging.info("Fetched event descriptions from allevents.in")

    return descriptions


if __name__ == "__main__":
    events = fetch_events_from_allevents(days=30)
    async def main():
        uploader = GoogleDriveUploader()

        async with aiohttp.ClientSession(trust_env=True) as session:
            tasks = []

            for event in events:
                url = event["original_img_name"]
                if url.lower() != "none":
                    task = asyncio.create_task(uploader.download_and_upload_image(url=url,session=session))
                    tasks.append(task)
                else:
                    tasks.append("NONE")
            results = await asyncio.gather(*tasks)
            print(results)
            for result in results:
                print(result)
    
    asyncio.run(main())
