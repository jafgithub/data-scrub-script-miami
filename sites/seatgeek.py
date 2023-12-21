import logging
from datetime import date, timedelta

import requests

from event import Event
# from utils import save_and_upload_image


def fetch_events_from_seatgeek(days=1, city="Miami"):
    url = "https://api.seatgeek.com/2/events/"

    try:
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        end_date_str = end_date.strftime("%Y-%m-%d")
        print(end_date_str)
        logging.info(
            f"Fetching events from seatgeek.com for {city} for the next {days} days."
        )
        results = []

        params = {
            "page": 0,
            "per_page": 50,
            "listing_count.gte": 1,
            "lat": 25.76168,
            "lon": -80.191788,
            "range": "50mi",
            "datetime_utc.lte": end_date_str,
            "sort": "datetime_local.asc",
            "client_id": "MTY2MnwxMzgzMzIwMTU4",
            # 'venue.city': 'miami'
        }
        pages = 1
        while True:
            params['page'] = pages
            print(params)
            response = requests.get(url, params=params)
            # print(response.url)
            if response.status_code == 200:
                data = response.json()
                meta = data.get("meta", {}).get('total')
                
                data = data.get("events", [])
                if not data:
                    break
                logging.info(f"Fetched {len(data)} events from allevents.in.")

                print(len(data))

                # print(record)
                for i, record in enumerate(data):
                    # stime = datetime.fromtimestamp(
                    #     int(record["start_time"]))
                    # etime = datetime.fromtimestamp(
                    #     int(record["end_time"]))
                    # f"{event['latitude']} {event['longitude']}"
                    try:
                        event_name = record["title"]
                        event_url = record["url"]
                        print(f"Event {i} : {event_url}")
                        venue = record["venue"].get("name", "")
                        performers = record["performers"]
                        if performers:
                            image_url = performers[0].get("image")

                            if not image_url:
                                image_url = "NONE"
                                # event_image = save_and_upload_image(
                                #     image_url, website_name="seatgeek.com"
                                # )

                                # if event_image == "NONE":
                                #     file_name = "NONE"
                                # else:
                                #     file_name, event_image = event_image
                                pass
                            # else:
                            #     event_image = "NONE"
                        else:
                            event_image = "NONE"
                        startdate_str = record["datetime_local"].split("T")
                        start_date = startdate_str[0]
                        end_time = "NONE"
                        start_time = startdate_str[1]
                        end_date = "NONE"
                        latitude = float(record["venue"]["location"]["lat"])
                        longitude = float(record["venue"]["location"]["lon"])
                        full_address = f"{record['venue']['name']}, {record['venue']['address']}, {record['venue']['display_location']} - {record['venue']['postal_code']}"
                        # print(full_address)
                        description = (
                            "NONE" if record["description"] == "" else record["description"]
                        )
                        categories = ", ".join(
                            [taxonomy["name"] for taxonomy in record["taxonomies"]]
                        )
                        ticket_price = record["stats"].get("median_price", 0)

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
                        # events.append(instance)
                        print(f"Event {i} processed successfully. {an_event['event_url']}")
                        logging.info(
                            f"Event {i} processed successfully. {an_event['event_url']}"
                        )
                    except KeyError:
                        logging.exception(
                            f"KeyError: occurred while processing Event {i}. url = {an_event['event_url']}"
                        )
                pages+=1
                # events = prepare_data_for_excel(events)

            else:
                logging.exception(f"Request failed with status code {response.status_code}")
                print("Request failed with status code", response.status_code)
            
        return results
 
    except Exception:
        logging.exception(f"An error occurred while fetching events from allevents.in:")
        print("An error occurred while fetching events from allevents.in:")


if __name__ == "__main__":
    results = fetch_events_from_seatgeek()
    print(results)
