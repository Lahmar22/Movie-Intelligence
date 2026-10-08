import re
import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Movie Intelligence", page_icon="🎬", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.analysis import getAllMovies


@st.cache_data
def load_movies():
    return pd.DataFrame(list(getAllMovies()))


@st.cache_resource
def load_models():
    models_dir = PROJECT_ROOT / "models"
    clustering = joblib.load(models_dir / "pipeline_clustering.joblib")
    if not callable(getattr(clustering, "predict", None)):
        raise TypeError(
            "pipeline_clustering.joblib ne contient pas un modèle prédictif. "
            "Réexécutez la dernière cellule de dashboard/visualisation.ipynb."
        )
    classification = joblib.load(models_dir / "high_engagement_model.joblib")
    return clustering, classification


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


st.title("🎬 Movie Intelligence")
st.caption("Explorez les films, leurs prédictions et leurs groupes thématiques.")

df = load_movies()
if df.empty:
    st.info("Aucun film disponible dans la base de données.")
    st.stop()

for column in ["vote_average", "popularity", "revenue", "budget", "runtime"]:
    if column not in df:
        df[column] = 0
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

if "release_date" not in df:
    df["release_date"] = pd.NaT
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df["release_year"] = df["release_date"].dt.year.fillna(0).astype(int)

for column in ["title", "overview", "genres"]:
    if column not in df:
        df[column] = "" if column != "genres" else [[] for _ in range(len(df))]
df["overview_clean"] = df["overview"].fillna("").map(clean_text)

clustering_model, classification_model = load_models()
classification_features = [
    "popularity",
    "runtime",
    "release_year",
    "vote_average",
    "budget",
    "revenue",
]
df["engagement_prediction"] = classification_model.predict(
    df[classification_features]
)
if hasattr(classification_model, "predict_proba"):
    probabilities = classification_model.predict_proba(
        df[classification_features]
    )
    df["prediction_confidence"] = probabilities.max(axis=1) * 100
else:
    df["prediction_confidence"] = 0.0
df["engagement_label"] = df["engagement_prediction"].map(
    {0: "Engagement faible", 1: "Engagement élevé"}
).fillna(df["engagement_prediction"].astype(str))
df["cluster"] = clustering_model.predict(df["overview_clean"])

st.sidebar.header("Filtres")
all_genres = sorted(
    {
        genre
        for genres in df["genres"]
        if isinstance(genres, list)
        for genre in genres
    }
)
selected_genre = st.sidebar.selectbox("Genre", ["Tous"] + all_genres)
filtered_df = df.copy()
if selected_genre != "Tous":
    filtered_df = filtered_df[
        filtered_df["genres"].map(
            lambda genres: isinstance(genres, list) and selected_genre in genres
        )
    ]
search = st.sidebar.text_input("Rechercher un film")
if search:
    filtered_df = filtered_df[
        filtered_df["title"].astype(str).str.contains(search, case=False, na=False)
    ]

if filtered_df.empty:
    st.info("Aucun film ne correspond aux filtres sélectionnés.")
    st.stop()

overview_tab, classification_tab, clusters_tab = st.tabs(
    ["Tableau de bord", "Classification", "Clusters"]
)

with overview_tab:
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Films", f"{len(filtered_df):,}")
    metric2.metric("Note moyenne", f"{filtered_df['vote_average'].mean():.2f}/10")
    metric3.metric("Popularité moyenne", f"{filtered_df['popularity'].mean():,.1f}")
    metric4.metric("Revenu moyen", f"${filtered_df['revenue'].mean():,.0f}")

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("Distribution des notes")
        ratings = (
            pd.cut(filtered_df["vote_average"], bins=10, include_lowest=True)
            .astype(str)
            .value_counts()
            .sort_index()
        )
        st.bar_chart(ratings)
    with chart2:
        st.subheader("Genres les plus fréquents")
        genre_counts = (
            filtered_df["genres"]
            .explode()
            .dropna()
            .value_counts()
            .head(10)
            .sort_values()
        )
        st.bar_chart(genre_counts)

    st.subheader("Films")
    st.dataframe(
        filtered_df[
            ["title", "release_year", "genres", "vote_average", "popularity", "revenue"]
        ].sort_values("popularity", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

with classification_tab:
    st.subheader("Prédiction de l’engagement")
    prediction_counts = filtered_df["engagement_label"].value_counts()
    classification_chart, classification_table = st.columns([1, 2])
    with classification_chart:
        st.bar_chart(prediction_counts)
    with classification_table:
        st.dataframe(
            filtered_df[
                ["title", "engagement_label", "prediction_confidence", "vote_count"]
                if "vote_count" in filtered_df
                else ["title", "engagement_label", "prediction_confidence"]
            ]
            .sort_values("prediction_confidence", ascending=False)
            .rename(
                columns={
                    "title": "Film",
                    "engagement_label": "Prédiction",
                    "prediction_confidence": "Confiance (%)",
                    "vote_count": "Nombre de votes",
                }
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Confiance (%)": st.column_config.NumberColumn(format="%.1f%%")
            },
        )

with clusters_tab:
    st.subheader("Groupes de films par synopsis")
    cluster_counts = filtered_df["cluster"].value_counts().sort_index()
    cluster_chart, cluster_scatter = st.columns([1, 2])
    with cluster_chart:
        st.bar_chart(cluster_counts)
    with cluster_scatter:
        st.scatter_chart(
            filtered_df.assign(cluster=filtered_df["cluster"].astype(str)),
            x="popularity",
            y="vote_average",
            color="cluster",
        )
    st.caption("Les numéros de cluster sont des groupes thématiques, pas un classement.")
