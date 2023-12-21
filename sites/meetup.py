import logging
from utils import make_request
from datetime import datetime, timedelta, timezone
import json
from event import Event

# Configure logging


def get_lat_long(city):
    url = "https://www.meetup.com/gql"

    headers = {
        'Content-Type': 'text/plain',
        'Cookie': 'MEETUP_INVALIDATE=iWGUcxc0WlG9coUK; MEETUP_INVALIDATE=dNVdWk3scz2H3n0g'
    }
    payload = json.dumps({
        "operationName": "locationWithInput",
        "variables": {
            "query": city
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "55a21eb6c958816ff0ae82a3253156d60595177b4f3c20b59ea696e97acc653d"
            }
        }
    })
    res = make_request(url=url, data=payload,
                       headers=headers, request_type="POST")
    lat = 0
    lng = 0
    if "searchedLocations" in res["data"]:
        lat = res["data"]["searchedLocations"][0]["lat"]
        lng = res["data"]["searchedLocations"][0]["lon"]
        return lat, lng


def fetch_events_from_meetup(days=2, city="Miami"):
    try:
        results = []
        print(days)
        lat, lng = get_lat_long(city)
        print(lat, lng)
        tz = timezone(timedelta(hours=-4))
        start_time = datetime.now()
        end_time = start_time + timedelta(days=int(days))
        start_time = start_time.replace(tzinfo=tz)
        end_time = end_time.replace(tzinfo=tz)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_time = start_time[:-2] + ":" + start_time[-2:]
        end_time = end_time[:-2] + ":" + end_time[-2:]

        url = "https://www.meetup.com/gql"

        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'MEETUP_INVALIDATE=UYS_7PWyA4iNHBs3'
        }
        payload = {
            "operationName": "categorySearch",
            "variables": {
                "first": 20,
                "lat": lat,
                "lon": lng,
                "topicCategoryId": None,
                "startDateRange": start_time,
                "endDateRange": end_time,
                "sortField": "DATETIME"
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "0aceed81313ebba814c0feadeda32f404147996091b6b77209353e2183b2dabb"
                }
            }
        }

        logging.info(f"Start Time: {start_time}")
        logging.info(f"End Time: {end_time}")
        response = make_request(
            url=url, request_type="POST", headers=headers, data=json.dumps(payload))
        hasNextPage = response["data"]["rankedEvents"]["pageInfo"]["hasNextPage"]
        cursor = response["data"]["rankedEvents"]["pageInfo"]["endCursor"]
        records = response["data"]["rankedEvents"]["edges"]
        payload["variables"]["after"] = cursor
        records = [record["node"] for record in records]
        while hasNextPage:
            response = make_request(
                url=url, headers=headers, request_type="POST", data=json.dumps(payload))
            hasNextPage = response["data"]["rankedEvents"]["pageInfo"]["hasNextPage"]
            cursor = response["data"]["rankedEvents"]["pageInfo"]["endCursor"]
            payload["variables"]["after"] = cursor
            _records = response["data"]["rankedEvents"]["edges"]
            tmp = [records.append(record["node"]) for record in _records]
        else:
            response = make_request(
                url=url, headers=headers, request_type="POST", data=json.dumps(payload))
            hasNextPage = response["data"]["rankedEvents"]["pageInfo"]["hasNextPage"]
            cursor = response["data"]["rankedEvents"]["pageInfo"]["endCursor"]
            payload["variables"]["after"] = cursor
            _records = response["data"]["rankedEvents"]["edges"]
            tmp = [records.append(record["node"]) for record in _records]

        print(len(records))
        for i, record in enumerate(records):
            try:
                address = f'{record["venue"]["address"] }, {record["venue"]["city"]}, {record["venue"]["state"]}'
                if address == ', , ':
                    address = record["venue"]["name"]
                image = record["images"][0]["source"] if len(
                    record["images"]) > 0 else "NONE"
                sdate = datetime.fromisoformat(record["dateTime"])
                edate = datetime.fromisoformat(record["endTime"])
                event = Event()
                event["title"] = record["title"]
                event["description"] = record["description"]
                if image == "NONE":
                    event["img"], event["original_img_name"] = ("NONE", "NONE")
                else:
                    # img_name, event["original_img_name"] = save_and_upload_image(
                    #     image, "meetup.com")
                    # event["img"] = f"images/event/{img_name}"
                    event["original_img_name"] = image
                event["place_name"] = record["venue"]["name"]
                event["address"] = address
                event["latitude"] = record["venue"]["lat"]
                event["longitude"] = record["venue"]["lng"]
                event["event category"] = "NONE"
                event["cover_img"] = event["img"]
                event["sdate"] = sdate.strftime("%Y-%m-%d")
                event["stime"] = sdate.strftime("%H:%M:%S")
                event["etime"] = edate.strftime("%H:%M:%S")
                event["edate"] = edate.strftime("%Y-%m-%d")
                event["event_url"] = record["eventUrl"]
                results.append(event)
                logging.info(
                    f"Event {i+1} processed successfully. {event['event_url']}"
                )
            except Exception:
                logging.exception(
                    "An error occurred while processing a record")
    except Exception:
        logging.exception("An error occurred")

    return results

# Example usage:
# events = fetch_events_from_meetup()


if __name__ == "__main__":
    fetch_events_from_meetup()
