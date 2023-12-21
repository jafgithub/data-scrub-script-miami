import json
import logging
from typing import List, Optional

from lxml.etree import _Element, _ElementTree
from lxml.html import HtmlElement

from event import Event
from utils import generate_dates, make_request, read_json



def extract_values(element_list: list[_Element], attribute="text") -> str:
    
    def val(st: str):
        if ("," == st.strip()) or (not st.strip()):
            return False
        else:
            return True
    if len(element_list) > 0:
        if attribute == "src":
            print(len(element_list))
            print(element_list)
            return element_list[0].get("src")
        else:
            element = element_list[0]
            text_list = element.xpath("descendant-or-self::text()")
            # this text_list may contains many elements which have \n\t so we remove those
            # print(text_list)
            return ", ".join(list(filter(val, text_list))).strip()
    else:
        return "NddNE"


def fetch_event_from_miamibeachfl(days=2, city=None):
    _XPATHS = read_json("/home/ubuntu/events-scrap/xpath/miamibeachfl.json")
    try:
        results = []
        dates = generate_dates(days=days, format="%Y-%m-%d")
        if len(dates) > 1:
            logging.info(f"Scraping events from {dates[0]} to {dates[-1]}")
        for date in dates:
            res = make_request(
                url=f"https://www.miamibeachfl.gov/events/{date}/", request_type="GET"
            )
            logging.info(f"Scraping events for: {date}.")
            if isinstance(res, _Element) or isinstance(res, _ElementTree) or isinstance(res, HtmlElement):
                # tree = etree.ElementTree(res)
                links = [i.get("href") for i in res.xpath(_XPATHS["page_links"])]

                logging.info(f"Found {len(links)} for {date}.")

                for i, link in enumerate(links):
                    res = make_request(url=link, request_type="GET")
                    title = extract_values(res.xpath(_XPATHS.get("page_title")))
                    start_date = extract_values(res.xpath(_XPATHS.get("start_date")))
                    # print(type(title[0]))
                    # print(type(start_date[0]))
                    end_date = extract_values(res.xpath(_XPATHS.get("end_date")))
                    img_link = extract_values(res.xpath(_XPATHS.get("img")),"src")
                    logging.info(f"Image link: {img_link}")
                    # if img_link != "NONE":
                    #     # file_name, event_image = save_and_upload_image(
                    #     #     img_link, "miamibeachfl.gov"
                    #     # )
                    
                        
                    desc = extract_values(res.xpath(_XPATHS.get("desc")))
                    category = extract_values(res.xpath(_XPATHS.get("category")))
                    venue = extract_values(res.xpath(_XPATHS.get("venue")))
                    address = extract_values(res.xpath(_XPATHS.get("address")))
                    organizer = extract_values(res.xpath(_XPATHS.get("organizer")))
                    an_event = Event()
                    an_event["title"] = title
                    # if img_link != "NONE":
                    #     an_event["img"] = f"images/event/{file_name}"
                    #     an_event["cover_img"] = f"images/event/{file_name}"
                    # else:
                    #     an_event["img"] = "NONE"
                    #     an_event["cover_img"] = "NONE"
                    an_event["sdate"] = start_date
                    an_event["stime"] = "NONE"
                    an_event["etime"] = "NONE"
                    an_event["edate"] = end_date
                    an_event["address"] = address or "NONE"
                    an_event["description"] = desc
                    an_event["disclaimer"] = "NONE"
                    an_event["latitude"] = "NONE"
                    an_event["longitude"] = "NONE"
                    an_event["event_url"] = link
                    an_event["place_name"] = venue
                    an_event["original_img_name"] = img_link
                    # if img_link != "NONE":
                    # else:
                    #     an_event["original_img_name"] = "NONE"
                    an_event["organizer"] = organizer or "NONE"
                    an_event["event category"] = category
                    results.append(an_event)

                    logging.info(
                        f"Event {i+1} processed successfully. {an_event['event_url']}"
                    )

    except Exception:
        logging.exception("An error occurred.")

    return results


if __name__ == "__main__":
    fetch_event_from_miamibeachfl()
