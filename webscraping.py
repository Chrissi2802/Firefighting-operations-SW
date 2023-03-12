#---------------------------------------------------------------------------------------------------#
# File name: webscraping.py                                                                         #
# Autor: Chrissi2802                                                                                #
# Created on: 29.01.2023                                                                            #
# Content: This file provides functions to scrape data from the web from KFV (Kreisfeuerwehrverband #
#          Schweinfurt).                                                                            #
#---------------------------------------------------------------------------------------------------#


import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from furl import furl
import logging
import pytz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(process)d - %(funcName)s - %(levelname)s - %(message)s')


def create_empty_df():
    """This function creates two empty DataFrames. One for the scraped data and one for the check data.

    Returns:
        df_gesamt (pandas DataFrame): empty DataFrame for the data
        df_check (pandas DataFrame): empty DataFrame for the checks
    """

    df_gesamt = pd.DataFrame(columns = ["Nr", "Alarmierungszeit", "Wochentag", "Einsatztyp", "Einsatzort", "Link_einsatz", 
                                        "Bild", "Kurzbericht", "Organisationen", "Content", "Text"])
    df_check = pd.DataFrame(columns = ["Datetime", "URL", "Erste_Nr", "Letzte_Nr", "IO"])

    return df_gesamt, df_check


def get_next_website(old_url):
    """This function creates a new URL from an old one by adding 10.

    Args:
        old_url (string): Old URL; e.g. "https://www.kfv-schweinfurt.de/index.php/einsaetze?start=0"

    Returns:
        url (string): New URL
        new_number (integer): The new number
    """

    url = furl(old_url)
    url.args["start"] = int(url.args["start"]) + 10
    new_number = int(url.args["start"])

    return url.url, new_number


def get_last_nr():
    """This function determines the last number of the last saved operation.

    Returns:
        nr (integer): Number of the last saved operation
    """

    df = pd.read_csv("./Dataset/einsätze_erweitert.csv")
    nr = int(df["Nr"].iloc[0])

    return nr


def extract_data(einsatz):
    """This function extracts the data from the HTML code.

    Args:
        einsatz (BeautifulSoup Tag): HTML code of the operation 

    Returns:
        dict_einsatz (dictionary): Contains all extracted data
    """

    # Split text into list
    einsatz_list = einsatz.get_text().split("\n")

    # Extract Alarmierungszeit
    einsatz_datum_zeit = einsatz_list[2].split(" ")
    datum = einsatz_datum_zeit[1]
    zeit = einsatz_datum_zeit[-1].split("Uhr")[0]      
    alarmierungszeit = datetime.strptime(datum + " " + zeit, "%d.%m.%Y %H:%M")  # pares date and time to datetime object

    # Weekday
    wochentag = alarmierungszeit.strftime("%A")
    
    # Extract Einsatztyp
    einsatztyp = einsatz_list[6]

    # Extract Einsatzort
    einsatzort = einsatz_list[9].split("\t")[0][1:]    # remove first space

    # Link to operation, link is in the first element and from this the link is extracted
    link_einsatz = str(einsatz).split('<a href="')[1].split('">')[0]

    # Image name, image name is in the first element and from this the name is extracted
    bild_name = str(einsatz).split("https://www.kfv-schweinfurt.de/images/")[1].split('"')[0].split("/")[-1]

    # Extract Kurzbericht
    kurzbericht = einsatz_list[23].split("\t")

    # check length of kurzbericht
    if len(kurzbericht) > 5:
        kurzbericht = kurzbericht[5]
    elif len(einsatz_list[24].split("\t")) > 5:   # if long location, then it slides to the next line
        kurzbericht = einsatz_list[24].split("\t")[5]
    else:   # no kurzbericht available
        kurzbericht = ""

    # Extract Organisationen
    einsatz_string = str(einsatz).split('<!-- <span class="label label-info"> --!>')[1:]    # first element is useless

    # add all organisations to a string seperated by ;
    organisationen = ";".join([organisation.split("<!-- </span>--!>")[0].lstrip()
                                for organisation in einsatz_string])

    # Data to dictionary
    dict_einsatz = {"Nr": None, "Alarmierungszeit": alarmierungszeit, "Wochentag": wochentag, "Einsatztyp": einsatztyp,
                    "Einsatzort": einsatzort, "Link_einsatz": link_einsatz, "Bild": bild_name, "Kurzbericht": kurzbericht,
                    "Organisationen": organisationen, "Content": str(einsatz), "Text": einsatz.get_text()}
            
    return dict_einsatz


def extract_data_feed(einsatz_feed):
    """This function extracts the data from the feed.

    Args:
        einsatz_feed (BeautifulSoup Tag): HTML code of the feed 

    Returns:
        dict_einsatz_feed (dictionary): Contains all extracted data from the feed
    """

    # Extract Nr from feed
    nr_feed = einsatz_feed.find("title").get_text()
    nr_feed = int(nr_feed.split(": ")[1].split(" - ")[0])

    # Extract Alarmierungszeit from feed
    alarmierungszeit_feed = einsatz_feed.find("pubDate").get_text()
    alarmierungszeit_feed = datetime.strptime(alarmierungszeit_feed, "%a, %d %b %Y %H:%M:%S %z")
    alarmierungszeit_feed = alarmierungszeit_feed.astimezone(pytz.utc).replace(tzinfo = None)

    # Data from feed to dictionary
    dict_einsatz_feed = {"Nr": nr_feed, "Alarmierungszeit": alarmierungszeit_feed}

    return dict_einsatz_feed


def webscraper(url, url_feed):
    """This function scraps all desired data from the KFV website.

    Args:
        url (string): URL where the data should be scraped
        url_feed (string): URL of the feed where the data should be scraped

    Returns:
        df (pandas DataFrame): Contains all scraped data
    """
    
    # crate df with columns
    df, _ = create_empty_df()

    # https://hidemy.name/de/proxy-list/
    # Use a proxy to avoid getting blocked
    proxies = [{"http": "http://161.35.39.82:3128"},    # United Kingdom London, HTTPS, hoch
               {"http": "http://169.55.89.6:80"}]       # United States, Ashburn, HTTPS, hoch
    
    # Website
    page = requests.get(url, proxies = proxies[1])
    logging.debug("Page status code: " + str(page.status_code))

    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find(id = "einsatzberichtList")
    einsätze = table.find_all("tr")

    # Feed website
    page_feed = requests.get(url_feed, proxies = proxies[1])
    logging.debug("Page feed status code: " + str(page_feed.status_code))

    soup_feed = BeautifulSoup(page_feed.content, "xml")
    einsätze_feed = soup_feed.find_all("item")

    for einsatz, einsatz_feed in zip(einsätze[1:-2], einsätze_feed):  # exclude first element and last two elements of the list

        # Extract necessary data
        dict_einsatz = extract_data(einsatz)
        dict_einsatz_feed = extract_data_feed(einsatz_feed)

        # check if Alarmierungszeit is the same
        if dict_einsatz["Alarmierungszeit"] == dict_einsatz_feed["Alarmierungszeit"]:
            dict_einsatz["Nr"] = dict_einsatz_feed["Nr"]
        else:
            raise Exception("Alarmierungszeit is not the same!")

        # concat new row to df
        df = pd.concat([df, pd.DataFrame(dict_einsatz, index = [0])], ignore_index = True)

    return df


def get_all_data(url, url_feed):
    """This function scraps all data from the website.

    Args:
        url (string): URL where the data should be scraped
        url_feed (string): URL of the feed where the data should be scraped
    """

    new_number = 0  # number of the current website
    letzte_nr = -1  # number of the last website, -1 because first website is nr 0
    df_gesamt, df_check = create_empty_df()

    try:
        # Last website: https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?start=15670
        while new_number <= 15670:    # TODO: Please change this number to the last website
            logging.info("Current Website: " + str(new_number))

            df = webscraper(url, url_feed)

            # first element in column Nr
            erste_nr = df["Nr"].iloc[0]
            io = 1

            # check if first_nr now and last_nr - 1 before are equal
            if new_number != 0:
                if erste_nr != letzte_nr - 1:
                    io = 0

            # last element in column Nr
            letzte_nr = df["Nr"].iloc[-1]

            # concat df_gesamt with df (new data)
            df_gesamt = pd.concat([df_gesamt, df], ignore_index = True)

            # concat df_check with new data
            df_check = pd.concat([df_check, pd.DataFrame({"Datetime": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), 
                                "URL": url, "Erste_Nr": erste_nr, "Letzte_Nr": letzte_nr, "IO": io}, 
                                index = [0])], ignore_index = True)

            # create new url and get new number for next website
            url, new_number = get_next_website(url)
            url_feed, _ = get_next_website(url_feed)

            # wait for random time between 1 and 30 seconds
            time.sleep(np.random.randint(1, 30))

    except Exception as e:
        logging.error(e)
    finally:
        # save df as csv
        df_gesamt.to_csv("./Dataset/einsätze.csv", index = False)

        # save df_check as csv
        df_check.to_csv("./Dataset/check.csv", index = False)


def get_specific_data(url, url_feed, nr):
    """This function scraps the latest data which has not been downloaded yet.

    Args:
        url (string): URL where the data should be scraped
        url_feed (string): URL of the feed where the data should be scraped
        nr (integer): Number of the last saved operation
    """

    new_number = 0  # number of the current website
    letzte_nr = nr + 1  # number of the last website
    df_gesamt, df_check = create_empty_df()
    
    try:
        while nr < letzte_nr:
            logging.info("Current Website: " + str(new_number))

            df = webscraper(url, url_feed)

            # first element in column Nr
            erste_nr = df["Nr"].iloc[0]
            io = 1

            # check if first_nr now and last_nr - 1 before are equal
            if new_number != 0:
                if erste_nr != letzte_nr - 1:
                    io = 0

            # last element in column Nr
            letzte_nr = df["Nr"].iloc[-1]

            # concat df_gesamt with df (new data)
            df_gesamt = pd.concat([df_gesamt, df], ignore_index = True)

            # concat df_check with new data
            df_check = pd.concat([df_check, pd.DataFrame({"Datetime": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), 
                                "URL": url, "Erste_Nr": erste_nr, "Letzte_Nr": letzte_nr, "IO": io}, 
                                index = [0])], ignore_index = True)

            # create new url and get new number for next website
            url, new_number = get_next_website(url)
            url_feed, _ = get_next_website(url_feed)

            # wait for random time between 1 and 30 seconds
            time.sleep(np.random.randint(1, 30))

    except Exception as e:
        logging.error(e)
    finally:
        # cut off df_total so that only the missing data is still in it
        df_gesamt = df_gesamt[df_gesamt["Nr"] > nr]

        # save df as csv
        df_gesamt.to_csv("./Dataset/einsätze_fehlend.csv", index = False)

        # save df_check as csv
        df_check.to_csv("./Dataset/check_fehlend.csv", index = False)


if __name__ == "__main__":
    
    # General webpage: https://www.kfv-schweinfurt.de/index.php/einsaetze
    # Current last webpage: https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?start=15670

    url = "https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?start=0"
    url_feed = "https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?format=feed&type=rss&start=0"

    # User input
    user_input = input("Do you want to get all data or only the latest data? (all/latest): ")

    if user_input == "all":
        get_all_data(url, url_feed)
    elif user_input == "latest":
        nr = get_last_nr()
        get_specific_data(url, url_feed, nr)
    
    