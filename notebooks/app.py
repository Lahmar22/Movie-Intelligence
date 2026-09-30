import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

import pandas as pd
from src.connectionDB import collection

def redData():
    movies = pd.read_json("data/data.json")
    # print(movies.dtypes)

    movies = movies.drop_duplicates(subset=["movie_id"])

    # print(movies["movie_id"].duplicated().sum())

    # incohérences
    # print(movies[movies["vote_average"] < 0])
    # print(movies[movies["vote_average"] > 10])
    # print(movies[movies["budget"] < 0])

    movies = movies[movies["release_date"] <= "2026-09-29"]

    movies["release_date"] = pd.to_datetime(
        movies["release_date"],
        errors="coerce"
    )
    # print((movies["release_date"] > "2026-09-29").sum())

    # print(movies.isnull().sum())

    movies = movies.dropna(subset=["release_date"])
    
    # print(movies.isnull().sum())
    movies = movies[
        movies["runtime"].notna() &
        (movies["runtime"] > 0)
    ]

    numeric_cols = [
        "movie_id",
        "runtime",
        "budget",
        "revenue",
        "popularity",
        "vote_average",
        "vote_count",
        "release_date"
    ]
    categorical_cols = [
        "original_language",
        "genres",
        "keywords"
    ]

    text_cols = [
        "title",
        "overview"
    ]

    return movies

    

    

def stockData():
    movies = redData()
    movies_dict = movies.to_dict(orient="records")

    collection.create_index(
        "movie_id",
        unique=True
    )
    for movie in movies_dict:
        collection.update_one(
            {"movie_id": movie["movie_id"]},
            {"$set": movie},
            upsert=True
        )
    print("movies is saved ")

stockData()
