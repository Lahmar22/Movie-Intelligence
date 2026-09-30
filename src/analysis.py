import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from src.connectionDB import collection

def getAllMovies():
    movies = collection.find(
        {},
        {"_id": 0}
    )

    return movies




