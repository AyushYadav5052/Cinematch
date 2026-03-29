import streamlit as st
import pickle
import pandas as pd
import requests
import numpy as np
import lzma  # Required for .xz files

# === CONFIGURATION ===
st.set_page_config(
    page_title="🎬 CineMatch",
    page_icon="🎥",
    layout="wide"
)

# === LOAD DATA ===
@st.cache_data
def load_data():
    try:
        # 1. Load the movies dictionary
        with open('movies_dict.pkl', 'rb') as f:
            movies_dict = pickle.load(f)
        movies = pd.DataFrame(movies_dict)
        
        # 2. Load the .xz compressed Similarity Matrix
        # Ensure this filename matches EXACTLY what you uploaded
        with lzma.open('similarity.pkl.xz', 'rb') as f:
            similarity = pickle.load(f, encoding='latin1')
            
        return movies, similarity
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

# Call the function to load your data
movies, similarity = load_data()

# === API FUNCTIONS ===
@st.cache_data(ttl=3600)
def fetch_movie_details(title):
    # Free OMDb API keys have a 1,000 daily request limit
    api_key = "55212a5c"  
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('Response') == 'False':
            return None

        poster = data.get('Poster')
        if not poster or poster == 'N/A':
            poster = 'https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Image'

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
    if similarity is None:
        return []
    try:
        # Finding the index of the selected movie
        movie_idx = movies[movies['title'].str.contains(movie_title, case=False, na=False)].index[0]
        
        # Getting similarity scores
        distances = similarity[movie_idx]
        
        # Sorting and getting top K indices (excluding the movie itself)
        indices = np.argsort(distances)[::-1][1:top_k + 1]
        
        recs = []
        for idx in indices:
            details = fetch_movie_details(movies.iloc[idx]['title'])
            if details:
                recs.append(details)
        return recs
    except Exception:
        return []

# === CSS STYLING ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
* { font-family: 'Poppins', sans-serif; }
.stApp {
    background: linear-gradient(135deg, #0c0c1a 0%, #1a1a2e 50%, #16213e 100%);
}
.main-header {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px;
    padding: 2rem;
    margin: 2rem 0;
    text-align: center;
}
.movie-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 24px;
    padding: 2rem;
    margin-bottom: 2rem;
}
h1 { 
    font-size: 3.5rem !important;
    background: linear-gradient(135deg, #ffffff 0%, #667eea 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)

# === HEADER & SEARCH ===
st.markdown("<div class='main-header'><h1>🎬 CineMatch</h1></div>", unsafe_allow_html=True)

if movies is not None:
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    if 'last_selected' not in st.session_state:
        st.session_state.last_selected = ""

    # Search Bar
    selected_movie = st.selectbox("Search for a movie:", options=sorted(movies['title'].values), index=None, placeholder="Search...")
    
    if st.button("🔍 MATCH ME"):
        if selected_movie:
            with st.spinner('Decompressing data and finding matches...'):
                st.session_state.recommendations = recommend(selected_movie)
                st.session_state.last_selected = selected_movie
        else:
            st.warning("Please select a movie!")

    # Results Display
    if st.session_state.recommendations:
        st.subheader(f"Because you liked {st.session_state.last_selected}:")
        for movie in st.session_state.recommendations:
            col_img, col_info = st.columns([1, 2.5])
            with col_img:
                st.image(movie['poster'], use_container_width=True)
            with col_info:
                st.markdown(f"""
                <div class='movie-card'>
                    <h2 style='color: white;'>{movie['title']} ({movie['year']})</h2>
                    <p style='color: #ffd700;'>⭐ {movie['rating']} | {movie['genre']}</p>
                    <p style='color: white;'><b>Director:</b> {movie['director']}</p>
                    <p style='color: rgba(255,255,255,0.9);'>{movie['plot']}</p>
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("The application is still loading the dataset. Please wait.")
