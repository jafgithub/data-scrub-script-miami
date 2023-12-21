import json
import logging
from datetime import datetime, timedelta

import requests
from event import Event

from utils import create_unique_object_id

# logging.basicConfig(filename='event_fetch.log', level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_events_from_ticketmaster(city="Miami", days=30):
    start_time = datetime.now()
    end_time = start_time + timedelta(days=days)
    start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    print(start_time)

    logging.info(f"Start Time: {start_time}, End Time: {end_time}")
    events = []
    url = f"https://app.ticketmaster.com/discovery/v2/events.json?apikey=iTkEPL9j8mfVUGeTgYSADIphb7pXDMOG&city={city.lower()}&size=200&page=0&startDateTime={start_time}&endDateTime={end_time}"
    print(url)
    try:
        results = []
        response = requests.get(url=url)

        response = response.json()
        response = response["_embedded"]["events"]
        logging.info(f"Number of events: {len(response)}")
        for i, record in enumerate(response):
            print(i)
            try:
                # img_name, img_link = save_and_upload_image(
                #     record["images"][4]["url"], "ticketmaster.com")
                
                if record.get("images") != []:
                    url = record["images"][4].get("url")
                an_event = Event()
                an_event['title'] = record.get("name")
                # an_event['img'] = f"images/event/{img_name}"  # data:img
                # an_event['cover_img'] = f"images/event/{img_name}"  # data:img_url
                an_event['sdate'] = record["dates"]["start"]["localDate"]  # data:startdate
                an_event['stime'] = record["dates"]["start"]["localTime"]  # data:starttime
                an_event['etime'] = "NONE"  # data:endtime
                an_event['address'] = f'{record["_embedded"]["venues"][0]["name"]} {record["_embedded"]["venues"][0]["postalCode"]}'  # data:event_address
                an_event['description'] = "NONE"  # data:description
                an_event['disclaimer'] = "NONE"  # data:desclaimer
                # data:latitude
                an_event['latitude'] = record["_embedded"]["venues"][0]["location"]["latitude"]
                an_event['longitude'] = record["_embedded"]["venues"][0]["location"]["longitude"]
                # data:place_name
                an_event['place_name'] = record["_embedded"]["venues"][0]["address"]["line1"]
                # data:categories
                an_event['event category'] = record["classifications"][0]["segment"]["name"]
                an_event['price'] = record.get("priceRanges")[0]["min"] if record.get("priceRange") else "NONE" # data:ticket_price
                an_event['is_soldout'] = "False"  # data:is_soldout
                an_event['event_url'] = record["url"]  # data:url
                an_event['edate'] = "NONE"  # data:endtime
                an_event['original_img_name'] = url  # data:original_img_name
                results.append(an_event)
                print(f"Event {i} processed successfully. {an_event['event_url']}")
                logging.info(
                    f"Event {i} processed successfully. {an_event['event_url']}")
            except KeyError:
                logging.exception(
                    f"KeyError: occurred while processing Event {i}. url = {an_event['event_url']}")
    except requests.exceptions.RequestException:
        logging.exception(f"Request Exception occurred.")
    except ValueError:
        logging.exception(
            f"ValueError: occurred while processing the response JSON.")
    except Exception:
        logging.exception(f"An error occurred.")

    return results


# fetch_events_from_ticketmaster()
