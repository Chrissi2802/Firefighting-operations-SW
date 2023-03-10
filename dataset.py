#---------------------------------------------------------------------------------------------------#
# File name: dataset.py                                                                             #
# Autor: Chrissi2802                                                                                #
# Created on: 29.01.2023                                                                            #
# Content: This file provides the datasets (Feuerwehreinsätze-SW) and prepares the data.            #
#---------------------------------------------------------------------------------------------------#


import pandas as pd
import geopy
from geopy.extra.rate_limiter import RateLimiter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(process)d - %(funcName)s - %(levelname)s - %(message)s')


def add_features(df):
    """This function adds features extracted directly from the data. For easier analysis.

    Args:
        df (pandas DataFrame): Contains the data

    Returns:
        df (pandas DataFrame): Contains all the data and extended features 
    """

    # Make Oragnisationen more easily available
    df["Organisationen_Liste"] = df["Organisationen"].apply(lambda x: str(x).split(";"))
    df["Organisationen_Anzahl"] = df["Organisationen_Liste"].apply(lambda x: len(x))

    # Extract date, time, week and day of year
    df["Jahr"] = df["Alarmierungszeit"].apply(lambda x: x.split("-")[0])
    df["Monat"] = df["Alarmierungszeit"].apply(lambda x: x.split("-")[1])
    df["Tag"] = df["Alarmierungszeit"].apply(lambda x: x.split("-")[2].split(" ")[0])
    df["Stunde"] = df["Alarmierungszeit"].apply(lambda x: x.split("-")[2].split(" ")[1].split(":")[0])
    df["Minute"] = df["Alarmierungszeit"].apply(lambda x: x.split("-")[2].split(" ")[1].split(":")[1])
    df["Kalenderwoche"] = pd.to_datetime(df["Alarmierungszeit"]).dt.isocalendar().week
    df["Jahrestag"] = pd.to_datetime(df["Alarmierungszeit"]).dt.dayofyear

    return df


def add_geodata_features(df):
    """This function adds concrete geodata. Is limited to Schweinfurt county, otherwise too many errors will appear.

    Args:
        df (pandas DataFrame): Contains the data

    Returns:
        df (pandas DataFrame): Contains all the data and extended features 
    """

    # Add address from Einsatzort
    df["Adresse_Einsatzort"] = "Germany, Bavaria, Schweinfurt, " + df["Einsatzort"]

    # Add coordinates from Einsatzort
    service = geopy.Nominatim(user_agent = "myGeocoder")
    df["Koordinaten_Einsatzort"] = df["Adresse_Einsatzort"].apply(RateLimiter(service.geocode, min_delay_seconds = 1))

    # Extract longitude and latitude
    df["Längengrad"] = df["Koordinaten_Einsatzort"].apply(lambda x: x.longitude if x is not None else None)
    df["Breitengrad"] = df["Koordinaten_Einsatzort"].apply(lambda x: x.latitude if x is not None else None)

    return df


def create_dataset():
    """This function creates the dataset. The files must be downloaded beforehand with webscraping.
    """

    # Read data
    df = pd.read_csv("./Dataset/einsätze.csv")
    logging.info("Shape of the scraped data: " + str(df.shape))

    # Feature Engineering
    df = add_features(df)

    # Do not query each Einsatzort individually, save time
    df_einsatzorte_unique = pd.DataFrame(df["Einsatzort"].unique(), columns = ["Einsatzort"])
    df_einsatzorte_unique = add_geodata_features(df_einsatzorte_unique)
    df_einsatzorte_unique.to_csv("./Dataset/einsatzorte_koordinaten.csv", index = False)    # save

    # Add coordinates of the Einsatzort
    df["Koordinaten_Einsatzort"] = df["Einsatzort"].map(df_einsatzorte_unique.set_index("Einsatzort")["Koordinaten_Einsatzort"])

    # Extract longitude and latitude
    df["Längengrad"] = df["Koordinaten_Einsatzort"].apply(lambda x: x.longitude if x is not None else None)
    df["Breitengrad"] = df["Koordinaten_Einsatzort"].apply(lambda x: x.latitude if x is not None else None)

    # Save df as csv
    df.to_csv("./Dataset/einsätze_erweitert.csv", index = False)
    logging.info("Shape of the extended data: " + str(df.shape))
    logging.info("The files 'einsätze.csv' and 'einsatzorte_koordinaten.csv' can be deleted.")


def extend_dataset():
    """This function extends the dataset with the new data. 
       The files must be downloaded beforehand with webscraping.
    """

    # Read data
    df = pd.read_csv("./Dataset/einsätze_erweitert.csv")
    df.to_csv("./Dataset/einsätze_erweitert_alt.csv", index = False)
    logging.info("Shape the existing data: " + str(df.shape))

    # Read in newly scraped data
    df_fehlend = pd.read_csv("./Dataset/einsätze_fehlend.csv")
    logging.info("Shape of the new data: " + str(df_fehlend.shape))
    
    # Feature Engineering
    df_fehlend = add_features(df_fehlend)
    df_fehlend = add_geodata_features(df_fehlend)

    # concat df and df_fehlend
    df = pd.concat([df, df_fehlend], axis = 0)
    df = df.sort_values(by = "Alarmierungszeit", ascending = False)
    df.to_csv("./Dataset/einsätze_erweitert.csv", index = False)
    logging.info("Shape of the combined data: " + str(df.shape))

    # Part of the csvs can be deleted
    logging.info("The files 'check.csv' and 'check_fehlend.csv' are not relevant any further.")
    logging.info("The files 'einsätze_erweitert_alt.csv' and 'einsätze_fehlend.csv' can be deleted.")


if __name__ == "__main__":

    # User input
    user_input = input("Do you want to create the dataset or extend the dataset? (create/extend): ")

    if user_input == "create":
        create_dataset()
    elif user_input == "extend":
        extend_dataset()   
    
