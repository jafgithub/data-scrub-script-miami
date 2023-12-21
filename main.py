import os
import datetime
import logging
import sys

import asyncio
import aiohttp
from aiohttp import ClientTimeout

from utils import GoogleDriveUploader, GoogleDriveUploaderAsync

from datetime import datetime

from args_parser import WEBSITE_FUNCTIONS, parse_arguments
# from utils import generate_xslx


def fetch_events(website, city, days):
    try:
        events_fetch_function = WEBSITE_FUNCTIONS.get(website)
        if events_fetch_function is None:
            raise ValueError("Invalid website name.")

        events = events_fetch_function(city=city.capitalize(), days=days)
        return events
    except Exception:
        logging.exception(f"An error occurred while fetching events.")


async def main():
    try:
        parser, args = parse_arguments()

        if len(sys.argv) == 1:
            parser.print_help()
            print("No arguments provided. Use -h or --help for usage information.")
            sys.exit(1)

        website = args.website
        city = args.city
        days = args.days
        
        # setup_logging()         ##### calling up logging function to intilize logging globally
        
        events = fetch_events(website, city, days)
        if events:
            logging.info(f"Number of events found: {len(events)}")
        else:
            logging.exception(f"No events found ")

        # uploader = GoogleDriveUploader()
        async with GoogleDriveUploaderAsync() as uploader:
            timeout = ClientTimeout(total=14400)
            async with aiohttp.ClientSession(trust_env=True,timeout=timeout) as session:
                tasks = []
                print(events)
                for event in events:
                    url = event["original_img_name"]

                    # print("URL in main", repr(url))
                    # if url.lower() != "none":
                    task = asyncio.create_task(uploader.download_and_upload_image(url=url, session=session))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                # print(results)

                for event,result in zip(events,results):
                    if isinstance(result,tuple):
                        
                        img_path,img_url = result
                        event["img"] = event["cover_img"] = img_path
                        event["original_img_name"] = img_url
                    else:
                        event["img"] = event["cover_img"] = event["original_img_name"] = "NONE"
                time_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace(":", "_")
                file_name = f"{website}_{time_now}.xlsx"
                await uploader.generate_xlsx(events=events, file_name=file_name)
                logging.info(f"Events fetched from {website} and XSLX uploaded successfully.")
    except Exception:
        logging.exception(f"An error occurred.")
        print("An error occurred.")

if __name__ == "__main__":
    asyncio.run(main())
