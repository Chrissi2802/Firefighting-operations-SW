#---------------------------------------------------------------------------------------------------#
# File name: test.py                                                                                #
# Autor: Chrissi2802                                                                                #
# Created on: 06.03.2023                                                                            #
# Content: This file provides the unittests for the project.                                        #
#---------------------------------------------------------------------------------------------------#


import pandas as pd
import unittest

from selftest import Selftest
from webscraping import create_empty_df, get_next_website, get_last_nr, webscraper
from dataset import add_features, add_geodata_features
from text_classification_ml import data_preprocessing


class Test_webscraping(unittest.TestCase):
    """This class tests the functions of the webscraping.py file.

    Args:
        unittest (unittest TestCase): Unittest TestCase
    """
    
    def test_create_empty_df(self):
        """This method tests the create_empty_df function.
        """

        df_gesamt, df_check = create_empty_df()

        # check if they are dataframes
        self.assertTrue(isinstance(df_gesamt, pd.DataFrame))
        self.assertTrue(isinstance(df_check, pd.DataFrame))

        # check if they are empty
        self.assertTrue(df_gesamt.empty)
        self.assertTrue(df_check.empty)

        # check the shape of the daaframes
        self.assertEqual(df_gesamt.shape, (0, 11))
        self.assertEqual(df_check.shape, (0, 5))

    def test_get_next_website(self):
        """This method tests the get_next_website function.
        """

        url, nr = get_next_website(url_0)
        url_feed, _ = get_next_website(url_1)

        self.assertTrue(isinstance(url, str))   # check if the url is a string
        self.assertTrue(isinstance(url_feed, str))   # check if the url_feed is a string
        self.assertTrue(isinstance(nr, int))    # check if the nr is an integer

        # check if the url is correct
        self.assertEqual(url, "https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?start=10")
        self.assertEqual(url_feed, "https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?format=feed&type=rss&start=10")
        self.assertEqual(nr, 10)    # check if the nr is correct

    def test_get_last_nr(self):
        """This method tests the get_last_nr function.
        """

        nr = get_last_nr()

        self.assertTrue(isinstance(nr, int))    # check if the nr is an integer
        self.assertEqual(nr, 1352)   # check if the nr is correct

    def test_webscraper(self):
        """This method tests the webscraper function.
        """

        df = webscraper(url_0, url_1)

        self.assertTrue(isinstance(df, pd.DataFrame))   # check if the df is a dataframe
        self.assertEqual(df.shape, (10, 11))    # check if the shape is correct


class Test_dataset(unittest.TestCase):
    """This class tests the functions of the dataset.py file.

    Args:
        unittest (unittest TestCase): Unittest TestCase
    """

    def test_add_features(self):
        """This method tests the add_features function.
        """

        df = pd.DataFrame(data=[example_data], columns=example_columns)
        df = add_features(df)

        self.assertTrue(isinstance(df, pd.DataFrame))   # check if the df is a dataframe
        self.assertEqual(df.shape, (1, 20))             # check if the shape is correct

    def test_add_geodata_features(self):
        """This method tests the add_geodata_features function.
        """

        df = pd.DataFrame(data=[example_data], columns=example_columns)
        df = add_geodata_features(df)

        self.assertTrue(isinstance(df, pd.DataFrame))   # check if the df is a dataframe
        self.assertEqual(df.shape, (1, 15))             # check if the shape is correct


class Test_machine_learning(unittest.TestCase):
    """This class tests the functions of the text_classification_ml.py file.

    Args:
        unittest (unittest TestCase): Unittest TestCase
    """

    def test_data_preprocessing(self):
        """This method tests the data_preprocessing function.
        """

        df = pd.DataFrame(data=[example_data], columns=example_columns)
        df = data_preprocessing(df, classes)

        self.assertTrue(isinstance(df, pd.DataFrame))   # check if the df is a dataframe
        self.assertEqual(df.shape, (1, 11))             # check if the shape is correct
        self.assertTrue(df["Einsatztyp"].dtype == "int64")  # check if column Einsatztyp is numeric
        self.assertTrue(df["Kurzbericht"].str.islower().all() == True)  # check if all characters in colum Kurzbericht are lower case


if __name__ == "__main__":

    url_0 = "https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?start=0"
    url_1 = "https://www.kfv-schweinfurt.de/index.php/einsaetze/einsatzarchiv?format=feed&type=rss&start=0"
    example_data = [1352, "2022-12-31 21:55:00", "Saturday", "Brand", "Heidenfeld", 
                    "/index.php/einsaetze/einsatzbericht/40822", "nopic.png", "Brand am Gebäude", 
                    "FF Gochsheim;FL Schweinfurt-Land 4/4;FF Röthlein;FF Heidenfeld;FL Schweinfurt-Land 1;FF Grafenrheinfeld;FL Schweinfurt-Land 4", 
                    "Content", "Text"]
    	
    example_columns = ["Nr", "Alarmierungszeit", "Wochentag", "Einsatztyp", "Einsatzort", "Link_einsatz", 
                       "Bild", "Kurzbericht", "Organisationen", "Content", "Text"]
    classes = ["Technische Hilfe", "Brand"]

    Selftest()
    unittest.main()

