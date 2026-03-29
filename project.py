import streamlit as st
import pickle
import pandas as pd
import requests
import numpy as np
import gzip
# === CONFIGURATION ===
st.set_page_config(
    page_title="🎬 CineMatch",
    page_icon="🎥",
    layout="wide"
)


# === Load Data ===
@st.cache_data
def load_data():
    # Note: Ensure these files exist in your directory
    movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    

with gzip.open('similarity_compressed.pkl.gz', 'rb') as f:
    similarity = pickle.load(f)
    return movies, similarity


movies, similarity = load_data()


# === API Functions ===
@st.cache_data(ttl=3600)
def fetch_movie_details(title):
    api_key = "55212a5c"  # Your OMDb API Key
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('Response') == 'False':
            return None

        poster = data.get('Poster', 'https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Image')

        # EXTRACTING NEW FIELDS: Director and Actors (Cast)
        return {
            "title": data.get('Title', title),
            "year": data.get('Year', 'N/A'),
            "rating": data.get('imdbRating', 'N/A'),
            "genre": data.get('Genre', 'N/A'),
            "director": data.get('Director', 'Unknown'),
            "cast": data.get('Actors', 'Information unavailable'),
            "plot": data.get('Plot', 'No description available.'),
            "poster": poster
        }
    except:
        return None


def recommend(movie_title, top_k=5):
    try:
        movie_idx = movies[movies['title'].str.contains(movie_title, case=False, na=False)].index[0]
        distances = similarity[movie_idx]
        indices = np.argsort(distances)[::-1][1:top_k + 1]
        recs = []
        for idx in indices:
            details = fetch_movie_details(movies.iloc[idx]['title'])
            if details:
                recs.append(details)
        return recs[:top_k]
    except:
        return []


# === CSS STYLING ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
* { font-family: 'Poppins', sans-serif; }
body {
    background: linear-gradient(135deg, #0c0c1a 0%, #1a1a2e 50%, #16213e 100%);
    background-attachment: fixed;
}
.main-header {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px;
    padding: 2rem;
    margin: 2rem 0;
}
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 24px;
    padding: 3rem;
    margin: 1rem 0;
    position: relative;
    overflow: hidden;
}
.input-section {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 20px;
    padding: 2.5rem;
    margin: 2rem 0;
}
.movie-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 24px;
    padding: 2rem;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}
.movie-poster {
    width: 100%;
    border-radius: 20px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.3);
}
.meta-label {
    color: #667eea;
    font-weight: 600;
    font-size: 0.9rem;
    text-transform: uppercase;
    margin-right: 5px;
}
h1 { 
    font-size: 3.5rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# === HEADER & SEARCH ===
st.markdown("<div class='main-header'><h1>🎬 CineMatch</h1></div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_movie = st.selectbox("", options=sorted(movies['title'].values), index=None,
                                      placeholder="Search for a movie you love...")
    with col2:
        if st.button("🔍 **MATCH ME**"):
            if selected_movie:
                st.session_state.recommendations = recommend(selected_movie)
                st.session_state.show_results = True
    st.markdown("</div>", unsafe_allow_html=True)

# === RESULTS SECTION ===
if st.session_state.get('show_results'):
    for movie in st.session_state.get('recommendations', []):
        col_img, col_info = st.columns([1, 2.5])

        with col_img:
            st.markdown(f"<img src='{movie['poster']}' class='movie-poster'>", unsafe_allow_html=True)

        with col_info:
            st.markdown(f"""
            <div class='movie-card'>
                <h3 style='color: white; margin: 0;'>{movie['title']} ({movie['year']})</h3>
                <p style='color: #ffd700; margin-bottom: 10px;'>⭐ {movie['rating']} | {movie['genre']}</p>
                <div style='margin-bottom: 10px;'>
                    <span class='meta-label'>Director:</span> <span style='color: white;'>{movie['director']}</span><br>
                    <span class='meta-label'>Cast:</span> <span style='color: white;'>{movie['cast']}</span>
                </div>
                <p style='color: rgba(255,255,255,0.8); font-size: 0.95rem;'>{movie['plot']}</p>
            </div>
            """, unsafe_allow_html=True)
        st.write("")  # Spacer
