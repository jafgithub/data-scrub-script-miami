import json
import logging
import os
import shutil
import sys
from ast import List
from datetime import datetime, timedelta
from io import BytesIO
from typing import Union
import aiohttp
import asyncio
import yarl

from aiogoogle import Aiogoogle
from aiogoogle.models import MediaUpload
from aiogoogle.auth.creds import ServiceAccountCreds

import pandas as pd
import requests
import validators
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from lxml import html
from lxml.etree import HTML, _Element, _ElementUnicodeResult



os.makedirs("/home/ubuntu/events-scrap/logs", exist_ok=True)
logging.basicConfig(
    filename=f'/home/ubuntu/events-scrap/logs/log_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s::%(funcName)s() - %(message)s",
    datefmt="%H:%M:%S",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

formatter = logging.Formatter(fmt="%(levelname)s - %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

# root = logging.getLogger()
# root.setLevel(logging.DEBUG)

# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# root.addHandler(handler)


def preprocess_date_string(date_string):
    # Replace some common abbreviations and symbols
    date_string = date_string.replace(",", "").replace("–", "-")
    # Split the date string into individual components
    date_parts = date_string.split()
    # Extract the day and month
    day = int(date_parts[0])
    if len(date_parts[1]) != 3:
        date_parts[1] = date_parts[1][:-1]
    month = datetime.strptime(date_parts[1], "%b").month
    year = datetime.now().year
    # Combine the components into a standardized format
    date_standardized = f"{year:04d}-{month:02d}-{day:02d}"
    return datetime.strptime(date_standardized, "%Y-%m-%d")


def create_unique_object_id():
    now = datetime.now()
    formatted_value = now.strftime("%y%m%d%f")
    return formatted_value


def make_request(
    url: str,
    request_type: str = "GET",
    headers: dict = None,
    params: dict = None,
    data: dict = None,
    session: requests.Session = None,
    **kwargs,
) -> Union[html.HtmlElement, dict, str, None]:
    try:
        if request_type.upper() == "GET":
            if session:
                response = session.get(url=url, headers=headers, params=params, **kwargs)
                # print(session.get("https://api.ipify.org").content)
            else:
                response = requests.get(url=url, headers=headers, params=params, **kwargs)
        elif request_type.upper() == "POST":
            response = requests.post(url=url, headers=headers, data=data, **kwargs)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                # If the content type is HTML, parse and return it as an lxml object
                parsed_html = html.fromstring(response.content)
                return parsed_html

            elif "application/json" in content_type:
                # If the content type is JSON, parse and return it as a dictionary
                return response.json()
            else:
                # If it's neither HTML nor JSON, return the raw content
                return response.content
        else:
            # Handle non-200 status codes here if needed
            logging.exception(f"Request failed with status code {response.status_code}")
            return None
    except Exception:
        # Handle any exceptions that occur during the request
        logging.exception(f"An error occurred during the request.")
        return None


def is_url(url: str = "https://www.google.com/"):
    return validators.url(url)


def generate_dates(days=30, format="%Y-%m-%d", return_date_obj=False) -> List:
    """Generates a list of dates according to days from today in the format `yyyy-mm-dd`.

    Args:
      days: The number of days to generate dates for.

    Returns:
      A list of dates in the format `yyyy-mm-dd`.
    """

    dates = []
    start_date = datetime.today()
    for i in range(days):
        date = start_date + timedelta(days=i)
        if return_date_obj:
            dates.append(date)
        else:
            dates.append(date.strftime(format))
    return dates


def read_json(file_path: str) -> dict:
    with open(file_path) as f:
        xpaths = json.loads(f.read())
    return xpaths


def extract_values(element_list: list[_Element], attribute="text") -> str:
    def val(st: str):
        if ("," == st.strip()) or (not st.strip()):
            return False
        else:
            return True

    if len(element_list):
        if attribute == "src":
            return element_list[0].get("src")
        else:
            element = element_list[0]
            if isinstance(element, _ElementUnicodeResult) or isinstance(element, str):
                return element
            text_list = element.xpath("descendant-or-self::text()")
            # this text_list may contains many elements which have \n\t so we remove those
            # print(text_list)
            return ", ".join(list(filter(val, text_list))).strip()
    else:
        return "NONE"


def get_lat_long(city):
    url = "https://www.meetup.com/gql"

    headers = {
        "Content-Type": "text/plain",
        "Cookie": "MEETUP_INVALIDATE=iWGUcxc0WlG9coUK; MEETUP_INVALIDATE=dNVdWk3scz2H3n0g",
    }
    payload = json.dumps(
        {
            "operationName": "locationWithInput",
            "variables": {"query": city},
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "55a21eb6c958816ff0ae82a3253156d60595177b4f3c20b59ea696e97acc653d",
                }
            },
        }
    )
    res = make_request(url=url, data=payload, headers=headers, request_type="POST")
    lat = 0
    lng = 0
    if "searchedLocations" in res["data"]:
        lat = res["data"]["searchedLocations"][0]["lat"]
        lng = res["data"]["searchedLocations"][0]["lon"]
        return lat, lng


def get_driver(is_eager=False, disable_images=False, is_none=False):
    service = ChromeService(executable_path="/home/ubuntu/events-scrap/chromedriver")

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--lang=en")
    # options.add_argument(
    #     "Mozilla/5.0 (Linux; Android 10; HD1913) AppleWebKit/537.36 (KHTML,"
    #     " like Gecko) Chrome/110.0.5481.153 Mobile Safari/537.36"
    #     " EdgA/110.0.1587.50"
    # )
    # options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36")

    if is_none:
        options.page_load_strategy = "none"
    if is_eager:
        options.page_load_strategy = "eager"  # https://www.selenium.dev/documentation/webdriver/drivers/options/#pageloadstrategy
    if disable_images:
        options.add_argument(
            "--blink-settings=imagesEnabled=false"
        )  # Disable image loading

    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    # driver = webdriver.Chrome(service=service, options=options)
    driver = WebDriver(service=service, options=options)
    driver.maximize_window()

    return driver


def get_file_extension_from_url(url):
    try:
        filename = url.split("/")[-1]
        file_extension = os.path.splitext(filename)[1]
        return file_extension
    except:
        return None

def save_image(url: str, website_name: str):
    # print(url)
    if url.startswith("http"):
        res = requests.get(url)
        # print(res.status_code)
        prefix = f'.{res.headers["Content-Type"].split("/")[1]}'

        if prefix.lower() in (
            ".jpeg",
            ".png",
            ".jpg",
            ".gif",
            ".tiff",
            ".webp",
            ".avif",
            ".apng",
            ".svg",
            ".bpm",
            ".ico",
            ".octet-stream",
        ):
            pass
        else:
            return "NONE"

        today = datetime.today()
        dir_name = f"scrap_results/{today.strftime('%Y-%m-%d')}/images/{website_name}/"
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if prefix.lower() == ".octet-stream":
            prefix = url[-4:]
        file_name = f"c{create_unique_object_id()}{prefix}"
        image_path = f"{dir_name}{file_name}"

        # with open(image_path, "wb") as file:
        #     file.write(res.content)
        # dir_name = f"scrap_results/{today.strftime('%Y-%m-%d')}"
        return file_name, dir_name
    else:
        return "NONE"


class GoogleDriveUploader:
    def __init__(
        self,
    ) -> None:
        # self._CREDS_FILE = read_json("./sadiq_cred.json")
        self._CREDS_FILE = read_json("/home/ubuntu/events-scrap/file-scraping-983c52577b59.json")
        
        self._MAIN_FOLDER_ID = (
            self._CREDS_FILE["main_folder_id"]["aws"]
            if self._CREDS_FILE["main_folder_id"]["is_running_on_aws"]
            else self._CREDS_FILE["main_folder_id"]["local"]
        )
        self._CREDS = self._CREDS_FILE["creds"]
        self._service = self._build_service()
        self._folder_state = {}
        self.timeout = aiohttp.ClientTimeout(total=12)
        self._folder_lock = asyncio.Lock()

    def _build_service(self):
        try:
            credentials = service_account.Credentials.from_service_account_info(
                self._CREDS, scopes=["https://www.googleapis.com/auth/drive"]
            )
            return build("drive", "v3", credentials=credentials)
        except Exception as e:
            logging.exception(
                f"An error occurred while building the Google Drive service: {str(e)}"
            )
            return None

    async def upload_file(self, file: BytesIO, file_name, mimetype, folder_id: str):
        """Upload a file to specific folder.

        Args:
            file (BytesIO): BytesIO file object
            mimetype (str): file's mimetype returned by download_image
            folder_id (str): folder_id of the file
        """
        try:
            if folder_id:
                parent_id = folder_id
            else:
                parent_id = self._MAIN_FOLDER_ID

            parent_id = folder_id or self._MAIN_FOLDER_ID
            media_body = MediaIoBaseUpload(fd=file, mimetype=mimetype)
            file_metadata = {
                "name": os.path.basename(file_name),
                "parents": [parent_id],
            }
            media = (
                self._service.files()
                .create(body=file_metadata, media_body=media_body, fields="id")
                .execute()
            )

            # media = await self.upload_file_main(file_metadata=file_metadata, media_body=media_body)

            file_id = media.get("id")
            file_link = f"https://drive.google.com/file/d/{file_id}"
            # logging.info(f"File uploaded successfully. File ID: {file_id}")
            logging.info(f"File link: {file_link}")
            return file_link
        except Exception:
            logging.exception("An error occured while uploading the file.")

    async def upload_file_main(self, file_metadata, media_body=""):
        if media_body:
            media = (
                self._service.files().create(body=file_metadata, fields="id").execute()
            )
        else:
            media = (
                self._service.files()
                .create(body=file_metadata, media_body=media_body, fields="id")
                .execute()
            )

        return media

    async def create_folder(self, folder_name, parent_folder_id=""):
            print(self._folder_state)
            if folder_name in self._folder_state:
                return self._folder_state[folder_name]
            try:
                if parent_folder_id:
                    pass
                else:
                    parent_folder_id = self._MAIN_FOLDER_ID

                async with self._folder_lock:  # Acquire the lock
                    response = (
                        self._service.files()
                        .list(
                            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents",
                            fields="files(id)",
                        )
                        .execute()
                    )

                    if len(response["files"]) == 0:
                        folder_metadata = {
                            "name": folder_name,
                            "mimeType": "application/vnd.google-apps.folder",
                            "parents": [parent_folder_id],
                        }
                        folder = (
                            self._service.files()
                            .create(body=folder_metadata, fields="id")
                            .execute()
                        )

                        # folder = await self.upload_file_main(file_metadata=folder_metadata)
                        folder_id = folder.get("id")
                        self._folder_state[folder_name] = folder_id
                    else:
                        folder_id = response["files"][0]["id"]
                        self._folder_state[folder_name] = folder_id

                return folder_id
            except Exception:
                logging.exception("An error occurred while creating the folder.")

    async def download_image(self, url: str, session: aiohttp.ClientSession):
        # print("URL ", repr(url))
        if not is_url(url):
            return "NddONE"
        try:
            p = datetime.now()

            VALID_MIME_TYPES = {
                "image/jpeg": ".jpeg",
                "image/png": ".png",
                "image/jpg": ".jpg",
                "image/gif": ".gif",
                "image/tiff": ".tiff",
                "image/webp": ".webp",
                "image/apng": ".apng",
                "image/svg+xml": ".svg",
                "application/octet-stream": get_file_extension_from_url(url=url)
            }
            url = yarl.URL(url,encoded=True)
            res = await session.request(method="GET", url=url)
            # print(url)
            # print(res.status)
            # with open("status.txt","a") as f:
            #     f.write(f"{res.status} - {url}\n")
            if res.status !=200:
                logging.exception(f"Request failed with status code {res}")
                return "NONE"
            # print("res", res)

            # permission_body = {"role": "writer", "type": "anyone"}
            # print(self._CREDS_FILE)
            # print(self._service.permissions().create(
            # fileId="12rbBMyeMXmbwndU5raLOZrZJsuYVJ2Ay", body=permission_body
            # ).execute())

            # mimetype = res.headers.get("Content-Type", "").lower()

            mimetype = res.headers.get("Content-Type").lower()

            if mimetype in VALID_MIME_TYPES:
                file_name = f"c{create_unique_object_id()}{VALID_MIME_TYPES[mimetype]}"
                # print(url)
                content = await res.read()
                # print(res.status)
                # print("time since upload started : ", datetime.now() - p)
                return BytesIO(content), file_name, mimetype
            else:
                return "NONggE"
        except asyncio.TimeoutError:
            logging.exception("Timeout error occurred while making the request.")
            return "NONE"
        except Exception:
            logging.exception(f"An error occurred while downloading the image:")
            return "NONE"

    async def download_and_upload_image(self, url: str, **kwargs):
        # print(self._folder_state)
        p = datetime.now()
        output = await self.download_image(url, **kwargs)
        print(url)
        if output == "NddONE" or output == None or output == 'NONE':
            return output
        else:
            # print("output: ",output)
            file, file_name, mimetype = output

            today = datetime.today()

            today_folder = today.strftime("%Y-%m-%d")
            folder_id = await self.create_folder(folder_name=today_folder)
            image_folder_id = await self.create_folder(
                folder_name="Images", parent_folder_id=folder_id
            )

            image_link = await self.upload_file(
                file=file,
                file_name=file_name,
                mimetype=mimetype,
                folder_id=image_folder_id,
            )
            with open("upload.txt","a") as f:
                f.write(f"image uploaded {url}\n{image_link}\n")
            print(image_link)

            print(datetime.now() - p)
            return f"images/event/{file_name}", image_link

    async def generate_xlsx(self, events: list, file_name):
        try:
            if isinstance(events, list) and events:
                dataframe = pd.DataFrame(events)
                # print(dataframe)
                excel_file = BytesIO()
                dataframe.to_excel(excel_file, index=False,engine="xlsxwriter")
                # print(excel_file.getvalue())
                # print(excel_file.tell())
                excel_file.seek(0)
                today_folder = datetime.today().strftime("%Y-%m-%d")

                folder_id = await self.create_folder(folder_name=today_folder)

                report_folder_id = await self.create_folder(
                    folder_name="Reports", parent_folder_id=folder_id
                )
                # fo = open("allevents.in_2023-10-16_13-38-45.xlsx", "wb")
                # fo.write(excel_file.getvalue())

                file_link = await self.upload_file(
                    file=excel_file,
                    file_name=file_name,
                    mimetype="application/vnd.ms-excel",  # mimetype for excel files
                    folder_id=report_folder_id,
                )

                logging.info(
                    f"XLSX File Successfully Uploaded to Google drive: {file_link}"
                )
            else:
                raise
        except Exception:
            logging.exception("An error occurred while generating XSLX.")


class GoogleDriveUploaderAsync:

    def __init__(self) -> None:
        self._CREDS_FILE = read_json("sadiq_cred.json")
        # self._CREDS_FILE = read_json("/home/ubuntu/events-scrap/file-scraping-983c52577b59.json")
        self._MAIN_FOLDER_ID = (
            self._CREDS_FILE["main_folder_id"]["aws"]
            if self._CREDS_FILE["main_folder_id"]["is_running_on_aws"]
            else self._CREDS_FILE["main_folder_id"]["local"]
        )
        # self._MAIN_FOLDER_ID = "1sUrqeL3WC7iPaHHqdCRCs93cGgDHGZSH"
        self._CREDS = self._CREDS_FILE["creds"]
        self._service = None
        self._CREDS = ServiceAccountCreds(**self._CREDS)
        self._folder_state = {}
        self._aiogoogle = Aiogoogle(service_account_creds=self._CREDS)
        self._service = None
        self._folder_lock = asyncio.Lock()
    
    async def _build_service(self):
        try:

            self._service = await self._aiogoogle.discover('drive', 'v3')
        except Exception as e:
                
            logging.exception(
                f"An error occurred while building the Google Drive service: {str(e)}"
            )
            return None
    
    async def upload_file(self, file: bytes, file_name:str, mimetype:str, folder_id:str):
        if self._service is None:
            await self._build_service()

        try:
            
            if folder_id:
                parent_id = folder_id
            else:
                parent_id = self._MAIN_FOLDER_ID
            
            # media_body = MediaUpload(file)
            file_metadata = {
                "name": file_name,
                "parents": [parent_id],
            }

            upload_req = self._service.files.create(json=file_metadata,upload_file=file, fields="id")
            upload_req.upload_file_content_type = mimetype
            # print(upload_req)
            # print(type(upload_req))
            # upload_req.upload_file_content_type = mimetype
            # media = await self._aiogoogle.as_service_account(
            #     self._service.files.create(uri_params=file_metadata, data=file, fields="id")
            # )
            media = await self._aiogoogle.as_service_account(
                upload_req
            )
            file_id = media.get("id")
            file_link = f"https://drive.google.com/file/d/{file_id}"
            logging.info(f"File link: {file_link}")
            return file_link
        except Exception as e:
            logging.error("An error occured while uploading the file.")


    async def create_folder(self, folder_name, parent_folder_id=""):

        if self._service is None:
            await self._build_service()
        
        async with self._folder_lock:  # Acquire the lock
            # print(folder_name)
            if folder_name in self._folder_state:
                return self._folder_state[folder_name]
            try:
                if parent_folder_id:
                    pass
                else:
                    parent_folder_id = self._MAIN_FOLDER_ID

                # response = (
                #     self._service.files()
                #     .list(
                #         q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents",
                #         fields="files(id)",
                #     )
                #     .execute()
                # )
                # print(self._CREDS)
                # async with Aiogoogle(user_creds=self._CREDS) as aiogoogle:
                #     drive_v3 = await aiogoogle.discover('drive', 'v3')
                #     drive_v3
                response = await self._aiogoogle.as_service_account(
                self._service.files.list(
                    q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents",
                    fields="files(id)",
                ))

                if len(response["files"]) == 0:
                    folder_metadata = {
                        "name": folder_name,
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [parent_folder_id],
                    }
                    # folder = (
                    #     self._service.files()
                    #     .create(body=folder_metadata, fields="id")
                    #     .execute()
                    # )
                    
                    folder = await self._aiogoogle.as_service_account(
                        self._service.files
                        .create(json=folder_metadata, fields="id")
                    )

                    # folder = await self.upload_file_main(file_metadata=folder_metadata)
                    folder_id = folder.get("id")
                    self._folder_state[folder_name] = folder_id
                else:
                    folder_id = response["files"][0]["id"]
                    self._folder_state[folder_name] = folder_id

                return folder_id
            except Exception:
                logging.exception("An error occurred while creating the folder.")


    async def download_image(self, url: str, session: aiohttp.ClientSession):
        # print("URL ", repr(url))
        if not is_url(url):
            return "NONE"
        try:
            p = datetime.now()

            VALID_MIME_TYPES = {
                "image/jpeg": ".jpeg",
                "image/png": ".png",
                "image/jpg": ".jpg",
                "image/gif": ".gif",
                "image/tiff": ".tiff",
                "image/webp": ".webp",
                "image/apng": ".apng",
                "image/svg+xml": ".svg",
                "application/octet-stream": get_file_extension_from_url(url=url),
            }
            url = yarl.URL(url, encoded=True)
            res = await session.request(method="GET", url=url)
            logging.info(f"Image url: {url} Status code: {res.status}")
            if res.status != 200:
                logging.exception(f"Request failed with status code {res}")
                return "NONE"
            # print("res", res)

            # permission_body = {"role": "writer", "type": "anyone"}
            # print(self._CREDS_FILE)
            # print(self._service.permissions().create(
            # fileId="12rbBMyeMXmbwndU5raLOZrZJsuYVJ2Ay", body=permission_body
            # ).execute())

            # mimetype = res.headers.get("Content-Type", "").lower()

            mimetype = res.headers.get("Content-Type").lower()

            if mimetype in VALID_MIME_TYPES:
                # file_name = f"{str(count)}{VALID_MIME_TYPES[mimetype]}"
                file_name = f"c{create_unique_object_id()}{VALID_MIME_TYPES[mimetype]}"
                # print(url)
                content = await res.read()
                # print(res.status)
                # print("time since upload started : ", datetime.now() - p)
                return content, file_name, mimetype
            else:
                return "NONE"
        except asyncio.TimeoutError:
            logging.exception("Timeout error occurred while making the request.")
            return "NONE"
        except Exception:
            logging.exception(f"An error occurred while downloading the image:")
            return "NONE"

    async def download_and_upload_image(self, url: str, **kwargs):
        
        if is_url(url):
            # print(self._folder_state)
            
            p = datetime.now()
            output = await self.download_image(url, **kwargs)
            # print(url)
            if not isinstance(output, tuple):
                return "NONE", "NONE"
            else:
                # print("output: ",output)
                file, file_name, mimetype = output

                today = datetime.today()

                today_folder = today.strftime("%Y-%m-%d")
                folder_id = await self.create_folder(folder_name=today_folder)
                # print(folder_id)
                image_folder_id = await self.create_folder(
                    folder_name="Images", parent_folder_id=folder_id
                )
                
                # print("image_folder_id: ", image_folder_id)

                image_link = await self.upload_file(
                    file=file,
                    file_name=file_name,
                    mimetype=mimetype,
                    folder_id=image_folder_id,
                )

                print("time since image upload started: ",datetime.now() - p)
                return f"images/event/{file_name}", image_link
        else:
            return "NONE", "NONE"

    async def generate_xlsx(self, events: list, file_name):
        try:
            if isinstance(events, list) and events:
                dataframe = pd.DataFrame(events)
                # print(dataframe)
                excel_file = BytesIO()
                dataframe.to_excel(excel_file, index=False,engine="xlsxwriter")
                # print(excel_file.getvalue())
                # print(excel_file.tell())
                excel_bytes = excel_file.getvalue()
                today_folder = datetime.today().strftime("%Y-%m-%d")

                folder_id = await self.create_folder(folder_name=today_folder)

                report_folder_id = await self.create_folder(
                    folder_name="Reports", parent_folder_id=folder_id
                )
                # fo = open("allevents.in_2023-10-16_13-38-45.xlsx", "wb")
                # fo.write(excel_file.getvalue())

                file_link = await self.upload_file(
                    file=excel_bytes,
                    file_name=file_name,
                    mimetype="application/vnd.ms-excel",  # mimetype for excel files
                    folder_id=report_folder_id,
                )

                logging.info(
                    f"XLSX File Successfully Uploaded to Google drive: {file_link}"
                )
            else:
                raise
        except Exception:
            logging.exception("An error occurred while generating XSLX.")

    async def __aexit__(self, *args):
        await self._aiogoogle.__aexit__(*args)
    
    async def __aenter__(self):
        # print("started")
        await self._aiogoogle.__aenter__()
        return self




if __name__ == "__main__":
    p = datetime.now()

    # image_url = "https://firebasestorage.googleapis.com/v0/b/clothing-store-2.appspot.com/o/prod_image%2Fprod_image%2FID-43ffd83b-9625-45dc-b6b2-9f359d266959-0.webp?alt=media"
    image_url = "https://img.evbuc.com/https%3A%2F%2Fcdn.evbuc.com%2Fimages%2F602272019%2F1430182031443%2F1%2Foriginal.20230920-130504?w=940&auto=format%2Ccompress&q=75&sharp=10&rect=0%2C15%2C1200%2C600&s=13645e838fd09f2552c8f8500410abec"
    # save_image(url=image_url, website_name="eventbrite.com")
    image_urls = [image_url] * 50
    
    

    async def main():
        # Create an instance of GoogleDriveUploader
        # uploader = GoogleDriveUploaderAsync()

        # Create a list to store tasks
        async with GoogleDriveUploaderAsync() as uploader:
            timeout = aiohttp.ClientTimeout(total=14400)
            async with aiohttp.ClientSession(trust_env=True,timeout=timeout) as session:
                tasks = []

                # Iterate through the image URLs
                for i, url in enumerate(image_urls):
                    # Create a task for downloading and uploading each image
                    task = asyncio.create_task(
                        uploader.download_and_upload_image(url=url, session=session)
                    )
                    tasks.append(task)
                    # print(task)

                # Gather all tasks to run them concurrently
                await asyncio.gather(*tasks)
            # await uploader.close()

    asyncio.run(main())
    
    print("final-time: ", datetime.now() - p)