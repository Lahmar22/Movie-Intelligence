import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

_session = requests.Session()


def _request_json(url, params=None):
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        raise RuntimeError("API_TOKEN is not set")

    response = _session.get(
        url,
        headers={
            "Authorization": f"Bearer {api_token}",
            "accept": "application/json"
        },
        params=params,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def getData():
    movies = []

    for page in range(1, 101):

        url = "https://api.themoviedb.org/3/discover/movie"

        params = {
            "page": page,
            "language": "en-US"
        }

        data = _request_json(url, params=params)

        movies.extend(data["results"])

    return movies


def getDataById(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    return _request_json(url)


def get_keywords(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords"
    return _request_json(url)


def extraData():

    data = getData()

    movies = []

    for movie in data:

        movie_id = movie["id"]

        movie_details = getDataById(movie_id)

        keyword_data = get_keywords(movie_id)

        movie_data = {
            "movie_id": movie_details["id"],
            "title": movie_details["title"],
            "overview": movie_details["overview"],
            "release_date": movie_details["release_date"],
            "runtime": movie_details["runtime"],
            "original_language": movie_details["original_language"],
            "genres": [
                genre["name"]
                for genre in movie_details["genres"]
            ],
            "keywords": [
                keyword["name"]
                for keyword in keyword_data["keywords"]
            ],
            "budget": movie_details["budget"],
            "revenue": movie_details["revenue"],
            "popularity": movie_details["popularity"],
            "vote_average": movie_details["vote_average"],
            "vote_count": movie_details["vote_count"]
        }

        movies.append(movie_data)

        print(f"Film récupéré : {movie_id}")

    with open("data/data.json", "w", encoding="utf-8") as file:

        json.dump(
            movies,
            file,
            indent=4,
            ensure_ascii=False
        )


if __name__ == "__main__":
    extraData()