import time
import logging
from myjdapi import Myjdapi

# Internal global instance of Myjdapi and device name hidden
api = Myjdapi()
jd_device = None

# These are the credentials and device name. You should ideally load them from a secure source or environment variables.
EMAIL = "rami.raghfan@gmail.com"
PASSWORD = "xxxx"
DEVICE_NAME = "xxxx"

MAX_RETRIES = 3
RETRY_DELAY = 5


def retry(func):
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retries += 1
                logging.error(f"Error: {e}. Retrying ({retries}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY)
        raise Exception(f"Failed after {MAX_RETRIES} retries.")

    return wrapper


@retry
def connect_to_jdownloader():
    """Connect to JDownloader API and set up the global jd_device."""
    global api, jd_device
    try:
        if not api.is_connected():
            api.connect(EMAIL, PASSWORD)
            logging.info("Connected successfully to JDownloader API.")
            jd_device = api.get_device(device_name=DEVICE_NAME)
        else:
            print("API already connected.")
        if jd_device is None:
            raise Exception("Failed to retrieve JDownloader device.")
        logging.info(f"Retrieved JDownloader device: {DEVICE_NAME}")
    except Exception as e:
        logging.error(f"Failed to connect to JDownloader API: {e}")
        raise


@retry
def get_jd_device():
    """Get the JDownloader device, assume connection is already established."""
    global jd_device
    if jd_device is None:
        raise Exception("No device connected. Ensure you're connected first.")
    return jd_device


def disconnect_jdownloader():
    """Disconnect from JDownloader."""
    global api  # Access the global api instance
    try:
        if api.is_connected():
            api.disconnect()
            logging.info("Disconnected from JDownloader API.")
        else:
            logging.info("No active connection found.")
    except Exception as e:
        logging.error(f"Error during disconnect: {e}")
