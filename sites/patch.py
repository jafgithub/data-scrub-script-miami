import logging
from datetime import datetime, timedelta
from event import Event
from bs4 import BeautifulSoup
from utils import make_request

# Configure logging
logging.basicConfig(filename='event_fetcher.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_events_from_patch(days=10, city="Miami") -> list[Event]:
    try:
        records = []
        results = []
        patch_id = get_patch_id(city=city)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        start_date = start_date.strftime("%Y-%m-%d")
        i = 1
        end_date = end_date.strftime("%Y-%m-%d")
        url = f"https://patch.com/api_v2/calendar_r/events?patchId={patch_id}&pageNumber={i}&startDate={start_date}&endDate={end_date}"
        logging.info(f'Fetching events from URL: {url}')
        res = make_request(url)
        res = res["results"]
        logging.info(f'Retrieved {len(res)} events from API')
        records.extend(res)

        while res:
            i += 1
            url = f"https://patch.com/api_v2/calendar_r/events?patchId={patch_id}&pageNumber={i}&startDate={start_date}&endDate={end_date}"
            res = make_request(url)
            res = res["results"]
            logging.info(f'Retrieved {len(res)} additional events from API')
            records.extend(res)

        logging.info(f'Total {len(records)} events retrieved')

        for i, record in enumerate(records):
            event = Event()
            lat = lng = image_name = image_url = description = ""
            address = record["address"]
            if address:
                lat, lng = address["latitude"], address["longitude"]
                _address = f'{address["name"]}, {address["streetAddress"]}, {address["city"]}, {address["region"]}, {address["country"]}, {address["postalCode"]}'
            if record.get("body"):
                description = BeautifulSoup(
                    record["body"], "html.parser").get_text()
            if record["ogImageUrl"]:
                # image_name, image_url = save_and_upload_image(
                #     record["ogImageUrl"], "patch.com")
                img_url = record["ogImageUrl"]
                event["original_img_name"] = img_url or "NONE"
            sdate = datetime.fromtimestamp(int(record["displayDateTimestamp"]))
            event["title"] = record["title"] or "NONE"
            event["sdate"] = sdate.strftime("%Y-%m-%d")
            event["stime"] = sdate.strftime("%H-%M-%S")
            event["address"] = _address or "NONE"
            event["description"] = description or "NONE"
            event["latitude"] = lat or "NONE"
            event["longitude"] = lng or "NONE"
            # event["place_name"] = (
            #     address["name"] if address else "NONE") or "NONE"
            event["place_name"] = address.get("name") or "NONE"
            event["event_url"] = f"https://www.patch.com{record['canonicalUrl']}" if record["canonicalUrl"] else "NONE"
            event["edate"] = "NONE"
            event["etime"] = "NONE"
            # event["img"] = event["cover_img"] = f"images/event/{image_name}" or "NONE"

            results.append(event)
            logging.info(
                f"Event {i+1} successfully fetched: {event['event_url']}")

        return results
    except Exception as e:
        logging.error(f'Error in fetch_events_from_patch: {str(e)}')
        raise


def get_patch_id(city):
    try:
        url = f"https://96oj6ivkei.execute-api.us-east-1.amazonaws.com/api/search?query=\"{city}\"&limit=1"
        headers = {
            'authority': '96oj6ivkei.execute-api.us-east-1.amazonaws.com',
            'accept': 'application/json'
        }
        res = make_request(url=url, headers=headers)
        if res:
            return res[0]["id"]
        else:
            return None
    except Exception as e:
        logging.error(f'Error in get_patch_id: {str(e)}')
        raise


if __name__ == '__main__':
    try:
        events = fetch_events_from_patch(days=2)
        # Do something with the retrieved events
    except Exception as e:
        logging.error(f'Error in main: {str(e)}')
