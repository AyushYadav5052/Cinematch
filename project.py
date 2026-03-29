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

# === LOAD DATA ===
@st.cache_data
def load_data():
    # Load the movies dictionary
    with open('movies_dict.pkl', 'rb') as f:
        movies_dict = pickle.load(f)
    movies = pd.DataFrame(movies_dict)
    
    # Load the compressed similarity matrix
    with gzip.open('similarity_compressed.pkl.gz', 'rb') as f:
        similarity = pickle.load(f)
        
    return movies, similarity

# Call the function to load your data
movies, similarity = load_data()

# === API FUNCTIONS ===
@st.cache_data(ttl=3600)
def fetch_movie_details(title):
    api_key = "55212a5c"  # Your OMDb API Key
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
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
    except Exception as e:
        st.error(f"Error in recommendation: {e}")
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
.input-section {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 20px;
    padding: 2.5rem;
    margin-bottom: 3rem;
}
.movie-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 24px;
    padding: 2rem;
    margin-bottom: 2rem;
}
.movie-poster {
    width: 100%;
    border-radius: 20px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.5);
}
.meta-label {
    color: #667eea;
    font-weight: 600;
    font-size: 0.9rem;
    text-transform: uppercase;
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

# Initialize session state for results
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []

with st.container():
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_movie = st.selectbox("", options=sorted(movies['title'].values), index=None,
                                     placeholder="Search for a movie you love...")
    with col2:
        if st.button("🔍 MATCH ME"):
            if selected_movie:
                with st.spinner('Finding the best matches for you...'):
                    st.session_state.recommendations = recommend(selected_movie)
            else:
                st.warning("Please select a movie first!")
    st.markdown("</div>", unsafe_allow_html=True)

# === RESULTS SECTION ===
if st.session_state.recommendations:
    st.subheader(f"Because you liked {selected_movie}:")
    for movie in st.session_state.recommendations:
        col_img, col_info = st.columns([1, 2.5])
        
        with col_img:
            st.image(movie['poster'], use_container_width=True)

        with col_info:
            st.markdown(f"""
            <div class='movie-card'>
                <h2 style='color: white; margin-top: 0;'>{movie['title']} ({movie['year']})</h2>
                <p style='color: #ffd700; font-size: 1.1rem;'>⭐ {movie['rating']} | {movie['genre']}</p>
                <p><span class='meta-label'>Director:</span> <span style='color: white;'>{movie['director']}</span></p>
                <p><span class='meta-label'>Cast:</span> <span style='color: white;'>{movie['cast']}</span></p>
                <hr style='border: 0.5px solid rgba(255,255,255,0.1);'>
                <p style='color: rgba(255,255,255,0.9);'>{movie['plot']}</p>
            </div>
            """, unsafe_allow_html=True)
