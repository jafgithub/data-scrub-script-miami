import argparse

from sites.allevents import fetch_events_from_allevents
from sites.eventbrite import fetch_events_from_eventbrite
from sites.google_events import fetch_events_from_google_events
from sites.miamiandbeaches import fetch_events_from_miami_and_beaches
from sites.seatgeek import fetch_events_from_seatgeek
from sites.ticketmaster import fetch_events_from_ticketmaster
from sites.miamibeachfl import fetch_event_from_miamibeachfl
from sites.tentimes import fetch_events_from_tentimes
from sites.miamionthecheap import fetch_events_from_miamionthecheap
from sites.meetup import fetch_events_from_meetup
from sites.local10 import fetch_event_from_local10
from sites.patch import fetch_events_from_patch
from sites.miamitimesonline import fetch_events_from_miamitimes


WEBSITE_FUNCTIONS = {
    "miamiandbeaches.com": fetch_events_from_miami_and_beaches,
    "eventbrite.com": fetch_events_from_eventbrite,
    "allevents.in": fetch_events_from_allevents,
    "googleevents": fetch_events_from_google_events,
    "ticketmaster.com": fetch_events_from_ticketmaster,
    "seatgeek.com": fetch_events_from_seatgeek,
    "miamibeachfl.gov":fetch_event_from_miamibeachfl,
    '10times.com': fetch_events_from_tentimes,
    'miamionthecheap.com': fetch_events_from_miamionthecheap,
    "meetup.com": fetch_events_from_meetup,
    "local10.com": fetch_event_from_local10,
    "patch.com": fetch_events_from_patch,
    "miamitimesonline.com": fetch_events_from_miamitimes
}

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Event web scraping Tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    scrapping_group = parser.add_argument_group(
        "Scraping arguments", description="Scraping related parameters"
    )

    scrapping_group.add_argument(
        "-w",
        "--website",
        metavar="WEBSITE",
        type=str,
        choices=WEBSITE_FUNCTIONS.keys(),
        help="Enter the name of the website:\n" + "\n".join([f"  - {choice}" for choice in WEBSITE_FUNCTIONS.keys()]),
    )

    scrapping_group.add_argument(
        "-c", "--city", metavar=None, type=str, default="Miami", help="Enter the name of the city"
    )

    scrapping_group.add_argument(
        "-d", "--days", metavar=None, type=int, default=1, help="Enter the number of days"
    )

    args = parser.parse_args()
    return parser, args
