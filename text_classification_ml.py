#---------------------------------------------------------------------------------------------------#
# File name: text_classification_ml.py                                                              #
# Autor: Chrissi2802                                                                                #
# Created on: 02.02.2023                                                                            #
# Content: This file provides functions for machine learning tasks for text classification          #
#          on the Feuerwehreinsätze-SW dataset.                                                     #
#---------------------------------------------------------------------------------------------------#
# Inspired by: https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html


import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.model_selection import train_test_split, GridSearchCV, RepeatedStratifiedKFold
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn import metrics
from sklearn.pipeline import Pipeline


def data_preprocessing(df, classes):
    """This function prepares the text data for the machine learning task.

    Args:
        df (pandas DataFrame): Entire data set
        classes (list): Einsatztypen, to be used

    Returns:
        df (pandas DataFrame): Reduced and preprocessed text dataset
    """

    # Data only if specific Einsatztyp
    df = df[df["Einsatztyp"].isin(classes)]

    # Convert Einsatztyp to number
    df["Einsatztyp"] = df["Einsatztyp"].apply(lambda x: classes.index(x))

    # Convert Kurzbericht to lower case strings
    df["Kurzbericht"] = df["Kurzbericht"].apply(lambda x: str(x).lower())

    # .,!?;: remove from Kurzbericht
    zeichen = [".", ",", "!", "?", ";", ":", "(", ")", "=", ">", "<", "}", "{", "[", "]", "/"]
    for i in zeichen:
        df["Kurzbericht"] = df["Kurzbericht"].apply(lambda x: str(x).replace(i, ""))

    return df


def distribute_labels_equally(df):
    """This function distributes the labels equally.

    Args:
        df (pandas DataFrame): Data set with preprocessed text data

    Returns:
        df_reduced (pandas DataFrame): Data set with equally distributed labels
        df_rest (pandas DataFrame): Data set with the rest of the defined labels
    """

    # Use only unique Kurzberichte
    df = df.drop_duplicates(subset="Kurzbericht", keep="first")

    # Determine the least common Einsatztyp and number 
    min_count = df["Einsatztyp"].value_counts().min()
    min_class = df["Einsatztyp"].value_counts().idxmin()

    # Create a new DataFrame with the least common Einsatztyp
    df_reduced = df[df["Einsatztyp"] == min_class]

    # Add the same number of Kurzberichte from every other Einsatztyp, randomly selected
    for i in range(df["Einsatztyp"].nunique()):
        if i != min_class:
            df_reduced = pd.concat([df_reduced, df[df["Einsatztyp"] == i].sample(n=min_count, random_state=28)])

    # New dataframe containing all other kurzberichte
    df_rest = df[~df["Kurzbericht"].isin(df_reduced["Kurzbericht"])]
    
    return df_reduced, df_rest


def prepare_data_ml(classes):
    """This function prepares the data for the machine learning task.

    Args:
        classes (list): Einsatztypen, to be used

    Returns:
        df_reduced (pandas DataFrame): Data set with equally distributed labels
        df_rest (pandas DataFrame): Data set with the rest of the defined labels
    """

    # Read data
    df = pd.read_csv("./Dataset/einsätze_erweitert.csv")

    # Interpret Organisationen_Liste column as a list
    df["Organisationen_Liste"] = df["Organisationen"].apply(lambda x: str(x).split(";"))

    # Preprocess data
    df_train_test = data_preprocessing(df, classes)
    df_reduced, df_rest = distribute_labels_equally(df_train_test)

    return df_reduced, df_rest


def ml_preprocessing_manually(X_train, X_test):
    """This function preprocesses the text data manually.

    Args:
        X_train (numpy array): Training data
        X_test (numpy array): Test data

    Returns:
        X_train_tfidf (numpy array): Transformed training data
        X_test_tfidf (numpy array): Transformed test data
        count_vect (sklearn CountVectorizer): Trained count vectorizer
        tfidf_transformer (sklearn TfidfTransformer): Trained tfidf transformer
    """

    # Count Vectorizer (Bag of Words)
    count_vect = CountVectorizer()
    X_train_counts = count_vect.fit_transform(X_train)
    X_test_counts = count_vect.transform(X_test)
    count_vect.vocabulary_.get(u'algorithm')

    # Term Frequency times Inverse Document Frequency (TF-IDF)
    tfidf_transformer = TfidfTransformer()
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    X_test_tfidf = tfidf_transformer.transform(X_test_counts)

    return X_train_tfidf.toarray(), X_test_tfidf.toarray(), count_vect, tfidf_transformer


def grid_search_text_clf(x, y):
    """This function performs a grid search on the text classifier / pipeline, to find the best hyperparameters.

    Args:
        x (numpy array, pandas DataFrame): Train and test data
        y (numpy array, pandas DataFrame): Train and test labels

    Returns:
        best_params (dictionary): Name of the tested parameter with the best value
    """

    # Create a pipeline with a count vectorizer, tfidf transformer and a passive aggressive classifier
    text_clf = Pipeline([("vect", CountVectorizer()),
                         ("tfidf", TfidfTransformer()),
                         ("clf", PassiveAggressiveClassifier())])

    # Because we are using a pipeline we need to prepend the parameters with the name of the
    # class of instance we want to provide the parameters for.
    param_grid = [
        {   
            "vect__ngram_range": [(1, 1), (1, 2), (2, 2)],
            "tfidf__norm": ["l1", "l2"],
            "clf__max_iter": [100, 1000, 10000],
            "clf__tol": [1e-3, 1e-4, 1e-5],
            "clf__early_stopping": [True, False],
            "clf__loss": ["hinge", "squared_hinge"]
        }
    ]
    
    # Using crossvalidation
    repeated_kfolds = RepeatedStratifiedKFold(n_splits = 5, n_repeats = 5)

    # Search for the best hyperparameters
    search = GridSearchCV(
        text_clf,
        param_grid,
        scoring = "accuracy",
        cv = repeated_kfolds,
        n_jobs = -1,
        return_train_score = False,
        verbose = 1,
        error_score = "raise"
    )

    search.fit(x, y)

    # Print the best score and the best parameters
    print("CV score: %0.2f" % search.best_score_)
    print("Best parameters:", search.best_params_)

    return search.best_params_


if __name__ == "__main__":
    
    # List of classes to be used
    classes = ["Technische Hilfe", "Brand"]

    df_reduced, df_rest = prepare_data_ml(classes)

    # Train Test Split
    X_train, X_test, y_train, y_test = train_test_split(df_reduced["Kurzbericht"], df_reduced["Einsatztyp"], 
        test_size=0.3, random_state=28)

    # y_train, y_test to numpy array
    y_train = np.array(y_train)
    y_test = np.array(y_test)

    # Automatic pipeline
    text_clf = Pipeline([("vect", CountVectorizer()),
                         ("tfidf", TfidfTransformer()),
                         ("clf", PassiveAggressiveClassifier())])

    # Train the classifier
    text_clf.fit(X_train, y_train)

    # Predict the test data and print the classification report
    predicted = text_clf.predict(X_test)
    print(metrics.classification_report(y_test, predicted, target_names=classes))
    
