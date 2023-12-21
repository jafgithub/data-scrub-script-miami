import json
import logging
from datetime import datetime, timedelta

from event import Event
from utils import get_lat_long, make_request


url = "https://portal.cityspark.com/v1/events/WPLG"

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site'
}


def fetch_event_from_local10(days=10, city="New York"):
    result = []

    start_time = datetime.now()
    end_time = start_time + timedelta(days=int(days))
    start_time = start_time.strftime("%Y-%m-%dT%H:%M")
    end_time = end_time.strftime("%Y-%m-%dT%H:%M")

    try:
        lat, lng = get_lat_long(city)
        logging.info(f'Latitude: {lat}, Longitude: {lng} for {city}')
    except Exception as e:
        logging.error(f'Error fetching latitude and longitude: {str(e)}')
        return result
    # print(start_time, end_time)
    payload = {
        "ppid": 8541,
        "start": start_time,
        "end": end_time,
        "labels": [],
        "pick": False,
        "tps": "21",
        "sparks": False,
        "sort": "Time",
        "category": [],
        "distance": 50,
        "lat": lat,
        "lng": lng,
        "search": "",
        "skip": 0,
        "defFilter": "all"
    }

    try:
        res = make_request(url=url, request_type="POST",
                           data=json.dumps(payload), headers=headers)
        records = res["Value"]
    except Exception as e:
        logging.error(f'Error fetching events: {str(e)}')
        return result

    while res["Value"]:
        try:
            payload["skip"] += 100
            logging.info(f'Skip = {payload["skip"]}')
            res = make_request(url=url, request_type="POST",
                               data=json.dumps(payload), headers=headers)
            if res["Value"]:
                records.extend(res["Value"])
                logging.info(f"Length = {len(res['Value'])}")
        except Exception as e:
            logging.error(f'Error fetching more events: {str(e)}')

    logging.info("Total Events: %d", len(records))
    for record in records:
        try:
            address = ""
            edate = None
            if record["Venue"]:
                address += f'{record["Venue"]}'
            if record["Address"]:
                address += f', {record["Address"]}'
            if record["CityState"]:
                address += f', {record["CityState"]}'
            if record["Zip"]:
                address += f', {record["Zip"]}'
            sdate = datetime.strptime(
                record["DateStart"], '%Y-%m-%dT%H:%M:%SZ')
            address = address.replace(", ", "", 1)
            if record["DateEnd"]:
                edate = datetime.strptime(
                    record["DateEnd"], '%Y-%m-%dT%H:%M:%SZ')
            event = Event()
            image_path = image_url = "NONE"
            if record["Images"]:
                # image_path, image_url = save_and_upload_image(
                #     record["Images"][0]["url"], website_name="local10.com")

                img_url = record["Images"][0]["url"] or "NONE"
                # print(img_url)
            else:
                img_url = "NONE"
            event["title"] = record["Name"] or "NONE"
            # event["img"] = image_path or "NONE"
            # event["cover_img"] = image_path or "NONE"
            event["sdate"] = sdate.strftime("%Y-%m-%d") or "NONE"
            event["stime"] = sdate.strftime("%H:%M:%S") or "NONE"
            event["address"] = address or "NONE"
            event["description"] = record["Description"] or "NONE"
            event["latitude"] = record["latitude"] or "NONE"
            event["longitude"] = record["longitude"] or "NONE"
            event["place_name"] = record["Venue"] or "NONE"
            event["price"] = record["Price"] or "NONE"
            if record["Links"]:
                event["event_url"] = record["Links"][0]["url"] or "NONE"
            else:
                event["event_url"] = "NONE"
            if edate:
                event["etime"] = edate.strftime("%H:%M:%S") or "NONE"
                event["edate"] = edate.strftime("%Y-%m-%d") or "NONE"
            else:
                event["etime"] = "NONE"
                event["edate"] = "NONE"
            # print(image_url)
            event["original_img_name"] = img_url or "NONE"
            result.append(event)
            # logging.info(record["PId"])
            # logging.info(record["Venue"])
        except Exception as e:
            logging.error(f'Error processing event: {str(e)}')

    print(len(records))
    return result


if __name__ == "__main__":
    fetch_event_from_local10()
