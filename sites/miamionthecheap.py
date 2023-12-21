import platform
import re

import logging
from driver import CustomWebDriver
import requests
from time import sleep
from typing import List
from lxml.html import HtmlElement
from lxml.etree import _Element, _ElementTree, _ElementStringResult, _ElementUnicodeResult
from lxml import etree
from urllib.parse import urlparse, unquote

from event import Event
from utils import (generate_dates, make_request, read_json,
                    is_url, generate_dates)



def extract_values(element_list):
    element_string = ""
    if element_list:
        if isinstance(element_list[0], (_ElementUnicodeResult, str, _ElementStringResult)):
            for element in element_list:
                element_string += element.strip()
        else:
            for element in element_list:
                temp_str = element.text
                if temp_str:
                    temp_str = temp_str.strip()
                    element_string += temp_str
        if element_string:
            return element_string
        else:
            return "NONE"
    else:                               
        return "NONE"


def fetch_events_from_miamionthecheap(days=1, *args, **kwargs):

    driver = CustomWebDriver(is_eager=False)
    _XPATHS = read_json("/home/ubuntu/events-scrap/xpath/miamionthecheap.json")

    datesrange = generate_dates(days=days, return_date_obj=True)
    results = []
    for date in datesrange:

        url = f"https://miamionthecheap.com/events/view-date/{date.strftime('%m-%d-%Y')}/"
        print(url)

        response = make_request(url=url)

        if len(response) or isinstance(response, (HtmlElement, _ElementTree, list)):

            events_div = response.xpath(_XPATHS['listpage']['events_div'])[0]
            print(events_div)

            if platform.system() == "Windows":
                date_str = "%A, %B %#d, %Y"
            else:
                date_str = "%A, %B %-d, %Y"
            events_list: List[_Element] = events_div.xpath(
                _XPATHS['listpage']['events'].format(date_str=date.strftime(date_str)))
            print(len(events_list))
            for i, event in enumerate(events_list[:]):
                an_event = Event()
                event_url = extract_values(event.xpath(
                    _XPATHS['listpage']['event_url']))
                event_title = extract_values(event.xpath(
                    _XPATHS['listpage']['event_title']))
                print(i, event_url, end='\n\n')
                if is_url(event_url):
                    event_detail_page = make_request(event_url)

                    if len(event_detail_page) or isinstance(
                        event_detail_page, (_Element,
                                            HtmlElement, _ElementTree)
                    ):

                        event_image = extract_values(event_detail_page.xpath(
                            _XPATHS['detailpage']['event_image']))
                        # event_details = extract_values(event_detail_page.xpath(_XPATHS['detailpage']['event_details']))
                        start_datatime = extract_values(event_detail_page.xpath(
                            _XPATHS['detailpage']['start_datetime']))
                        ticket_price = extract_values(event_detail_page.xpath(
                            _XPATHS['detailpage']['ticket_price']))
                        place_name = extract_values(event_detail_page.xpath(
                            _XPATHS['detailpage']['place_name']))
                        address = extract_values(event_detail_page.xpath(
                            _XPATHS['detailpage']['address']))
                        address_url = extract_values(event_detail_page.xpath(
                            _XPATHS['detailpage']['address_url']))
                        desc = extract_values(event_detail_page.xpath(
                            _XPATHS['detailpage']['desc']))
                        print(event_image, type(event_image))
                        # location_info = extract_values(event_detail_page.xpath(_XPATHS['detailpage']['location_info']))

                        # print("URL: ", event_url, "\nTITLE: ", event_title, "\nIMAGE: ", event_image, "\nDESC: ", desc
                        #     , "\nSTARTDATETIME: ", start_datatime,  "\nTICKETPRICE: ", ticket_price, "\nADDRESS: "
                        #     , address, "\nPLACENAME: ", place_name, "\nADDRESS_URL: ", address_url, sep=''
                        #     , end='\n\n\n\n\n\n')

                        if event_image == "NONE":
                            # an_event["img"],  an_event["original_img_name"] = (
                            #     "NONE", "NONE")
                            an_event['original_img_name'] = "NONE"
                            # an_event["cover_img"] = "NONE"
                        else:
                            # img_name, an_event["original_img_name"] = save_and_upload_image(
                            #     event_image, "miamionthecheap.com")
                            # an_event["img"] = an_event["cover_img"] = f"images/event/{img_name}"
                            
                            an_event['original_img_name'] = event_image
                an_event['title'] = event_title
                an_event['sdate'] = start_datatime
                an_event['stime'] = "NONE"
                an_event['etime'] = "NONE"
                an_event['address'] = address
                an_event['description'] = desc
                an_event['disclaimer'] = "NONE"
                an_event['latitude'] = "NONE"
                an_event['longitude'] = "NONE"
                an_event['place_name'] = place_name
                an_event['event category'] = "NONE"
                an_event['price'] = ticket_price
                an_event['event_url'] = event_url
                an_event['edate'] = "NONE"
                an_event['address_url'] = address_url
                # an_event['original_img_name'] = event_image

                results.append(an_event)
    driver = CustomWebDriver(is_eager=False)
    events_w_cords = scrap_geo_code(driver, results)
    return events_w_cords


def scrap_geo_code(driver: CustomWebDriver, events: list):
    # try:
    for i, event in enumerate(events):
        try:
            print(event['address_url'])
            location_link = event["address_url"]
            if location_link != "NONE":

                daddr = unquote(location_link.split("&daddr=")[1])
                location_link = f"https://www.google.com/maps?f=q&h1=en&daddr={daddr}"
                print("Location url: " + location_link)
                match = False
                driver.get(location_link)

                check_new_url = driver.wait_for(
                    "url_changes", location_link, timeout=60
                )

                if check_new_url:
                    new_url = driver.current_url
                    print("New url: " + new_url)

                    pattern = r"@([-+]?[0-9]*\.?[0-9]+),([-+]?[0-9]*\.?[0-9]+)"
                    match = re.search(pattern, new_url)

                    if match:
                        latitude = match.group(1)
                        longitude = match.group(2)
                        events[i]["latitude"] = latitude
                        events[i]["longitude"] = longitude
                        print(events[i]["latitude"], events[i]["longitude"])
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
            print(event)
            continue

    return events
    # except Exception:
    #     logging.exception
    #         "An unexpected error occurred while scraping geocode data")

    # Raise the error to propagate it further
    # raise e


if __name__ == "__main__":
    fetch_events_from_miamionthecheap()
