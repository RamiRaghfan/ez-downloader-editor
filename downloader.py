import subprocess
import threading
import time
import logging

WAIT_TIME = 15  # seconds to wait after adding links to LinkGrabber
CHECK_INTERVAL = 30  # seconds to wait between download status checks
TIMEOUT = 1200  # seconds to wait before timing out on download completion

VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.webm')


def add_url_to_linkgrabber(jd_device, task, index, download_directory):
    """Add the URL of a task to the JDownloader LinkGrabber."""
    response = jd_device.linkgrabber.add_links(params=[{
        "autostart": False,
        "links": task["url"],
        "packageName": f"task_{index + 1}",
        "destinationFolder": str(download_directory),
    }])
    return response


def move_package_to_downloads(jd_device, package_id):
    """Move a package from LinkGrabber to the Downloads list."""
    jd_device.linkgrabber.move_to_downloadlist(link_ids=[], package_ids=[package_id])
    logging.info(f"Package {package_id} moved to download list.")


def monitor_download_progress(jd_device, package_id, link, yt_dlp_path, check_interval=CHECK_INTERVAL, timeout=TIMEOUT):
    """Monitor the progress of a package in the Downloads list."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        links_query = jd_device.downloads.query_links(params=[{
            "packageUUIDs": [package_id],
            "status": True,
            "eta": True,
            "progress": True,
            "finished": True,
            "running": True,
        }])

        if not links_query:
            logging.warning(f"No links found in the Downloads list for package {package_id}.")
            return

        for link_detail in links_query:
            link_status = link_detail.get('status', 'Unknown')
            link_name = link_detail.get('name', 'Unnamed Link')
            logging.info(f"Link {link_name} - Status: {link_status}")

            if "unavailable" in link_status.lower():
                logging.warning(f"Link {link_name} is temporarily unavailable. Switching to yt-dlp.")
                download_with_yt_dlp(link["url"], yt_dlp_path, link_name)
                return

        time.sleep(check_interval)


def download_with_yt_dlp(url, yt_dlp_path, output_name):
    """Fallback to yt-dlp to download a file when JDownloader fails."""
    try:
        logging.info(f"Starting yt-dlp download for {url}")
        command = [
            yt_dlp_path,
            url,
            "-o", f"{output_name}.%(ext)s"
        ]
        subprocess.run(command, check=True)
        logging.info(f"yt-dlp successfully downloaded {output_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp failed to download {url}: {e}")


def process_download_task(jd_device, link, index, originals_directory, yt_dlp_path):
    """Process a single download task, monitoring its progress and falling back to yt-dlp if necessary."""
    try:
        add_url_to_linkgrabber(jd_device, link, index, originals_directory)
        logging.info(f"Link {index + 1}: URL {link['url']} added to LinkGrabber.")
        time.sleep(WAIT_TIME)

        package_name = f"link_{index + 1}"
        package_query = jd_device.linkgrabber.query_packages(params=[{
            "name": package_name,
            "status": True,
            "enabled": True,
        }])

        if not package_query:
            logging.warning(f"No package found for {package_name}.")
            return

        package_id = package_query[0]['uuid']
        move_package_to_downloads(jd_device, package_id)

        # Start monitoring in the background
        monitoring_thread = threading.Thread(
            target=monitor_download_progress,
            args=(jd_device, package_id, link, yt_dlp_path)
        )
        monitoring_thread.start()

    except Exception as e:
        logging.error(f"Error processing download task for link {link['url']}: {e}")
