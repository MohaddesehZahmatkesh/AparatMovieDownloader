import os
import time
import codecs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as Firefox_Options

# Constants
PLAYLIST_XPATH = "/html/body/div[2]/main/div/div/div[2]/ul"
VIDEO_META_XPATH = "//meta[@property='og:video']"
CLASS_SINGLE_PLAYLIST_TITLE = 'single-playlist__title'
CLASS_TITLE = 'title'

# functions
def check_firefox_installation():
    try:
        # Attempt to get the GeckoDriver path
        GeckoDriverManager().install()
        return True
    except Exception as e:
        print("Error:", e)
        print("Please install Firefox and try again.")
        return False

def create_firefox_driver(headless=True):
    firefox_options = Firefox_Options()
    firefox_options.headless = headless
    return webdriver.Firefox(options=firefox_options)

def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(expected_conditions.presence_of_element_located((by, value)))


def get_page_links(driver, url, output_file="Links.txt"):
    driver.get(url)
    page_links = []

    try:
        print("Waiting for playlist element...")
        playlist_element = WebDriverWait(driver, 20).until(
            expected_conditions.presence_of_element_located((By.XPATH, PLAYLIST_XPATH))
        )


        ul = driver.find_element(By.XPATH, PLAYLIST_XPATH)
        lis = ul.find_elements(By.TAG_NAME, "li")
        action = ActionChains(driver)
        aida = 0

        for li in lis:
            aida += 1
            a = li.find_element(By.TAG_NAME, "a")
            action.move_to_element(a).context_click().perform()
            a.send_keys(Keys.ESCAPE)
            size = a.size
            driver.execute_script("window.scrollTo(8, " + str(aida * (size['height'] + 20)) + "); ")
            time.sleep(0.1)
            print("Can Right Click On {} from {}".format(aida, len(lis)))

        for li in lis:
            a = li.find_element(By.TAG_NAME, "a")
            page_links.append(a.get_attribute("href"))

        if page_links:
            with codecs.open(output_file, "w", "utf-8") as f:
                f.write('\n'.join(page_links))
    except Exception as e:
        print("Error in get_page_links:", e)
    finally:
        # Do not quit the driver here, as it will be done in the main loop
        pass

def get_video_links(driver, url, input_file="Links.txt", output_file="download_links.txt"):
    try:
        driver.get(url)
        download_links = []

        with codecs.open(input_file, "r", "utf-8") as f:
            lines = f.readlines()
            for line in lines:
                driver.get(line)
                wait_for_element(driver, By.CLASS_NAME, CLASS_SINGLE_PLAYLIST_TITLE, timeout=100)
                meta = driver.find_element(By.XPATH, VIDEO_META_XPATH)
                content = meta.get_attribute("content")
                print(content)
                download_links.append(content)

        with codecs.open(output_file, "w", "utf-8") as f:
            f.write('\n'.join(download_links))
    finally:
        # Do not quit the driver here, as it will be done in the main loop
        pass

def convert_links(input_file="download_links.txt"):
    links = []

    # Convert all apt? files to mp4?
    with codecs.open(input_file, "r", "utf-8") as f:
        lines = f.readlines()
        for line in lines:
            links.append(line.replace(".apt?", ".mp4?"))

    with codecs.open(input_file, "w", "utf-8") as f:
        f.write(links)

def get_page_titles(driver, url, output_file="titles.txt"):
    driver.get(url)
    page_titles = []

    try:
        print("Waiting for playlist element...")
        playlist_element = WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, PLAYLIST_XPATH))
        )

        lis = playlist_element.find_elements(By.TAG_NAME, "li")
        action = ActionChains(driver)

        for li in lis:
            a = li.find_element(By.CLASS_NAME, CLASS_TITLE)
            page_titles.append(a.text)

        if len(page_titles) > 0:
            with codecs.open(output_file, "w", "utf-8") as f:
                for title in page_titles:
                    f.write(title + "\n")

    except TimeoutException as te:
        print(f"Timeout waiting for playlist element: {te}")
    except Exception as e:
        print(f"Error in get_page_titles: {e}")
    finally:
        # Do not quit the driver here, as it will be done in the main loop
        pass

def rename_files(driver, titles_file="titles.txt", links_file="download_links.txt", folder="movie"):
    # Create a list to store the titles
    titles = []

    try:
        with codecs.open(titles_file, "r", "utf-8") as f:
            lines = f.readlines()
            # Process each line
            for line in lines:
                # Replace invalid characters and append to the titles list
                name = line.strip().replace(" ", "_").replace(":", "_").replace("?", "_").replace(
                    "/", "_").replace("\\", "_").replace("*", "_").replace("\"", "_").replace("<", "_").replace(">", "_")
                titles.append(name)

        # Read all download links from the links file
        index = 0
        with codecs.open(links_file, "r", "utf-8") as f:
            lines = f.readlines()

            # Process each line
            for line in lines:
                # Separate filename from URL
                url = line.split("?")[0]
                filename = url.split("/")[-1]

                # Rename file
                os.rename(os.path.join(folder, filename),
                          os.path.join(folder, titles[index] + ".mp4"))
                index += 1
    finally:
        driver.quit()

if __name__ == "__main__":
    print("wait to create firefox driver")
    driver = create_firefox_driver()
    try:
        while True:
            print("Choose an option:")
            print("1. Get download links")
            print("2. Rename existing videos")
            option = input("Enter 1, 2: ")

            if option == "1":
                # Get user input for download links
                playlist_url = input("Enter the playlist URL: ")

                # Get page links
                get_page_links(driver, playlist_url)
                get_page_titles(driver, playlist_url)
                get_video_links(driver, playlist_url)
                convert_links()
                print("Download links have been found successfully. ;) ")
            elif option == "2":
                # Rename existing files
                rename_files(driver)
                print("Rename videos successfully. ;) ")
            else:
                print("Invalid option. Please enter 1, 2.")
    finally:
        driver.quit()