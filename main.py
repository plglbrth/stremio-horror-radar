import os
import requests
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Render injects this securely later. 
# Swap it for your actual key if you run it locally to test.
API_KEY = os.environ.get("TMDB_API_KEY", "YOUR_LOCAL_KEY_HERE")
BASE_URL = "https://api.themoviedb.org/3"

app = FastAPI()

# Stremio needs CORS enabled so your TV can actually talk to your server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)

MANIFEST = {
    "id": "com.oban.horrordrops",
    "version": "1.0.0",
    "name": "Upcoming Horror Radar",
    "description": "Tracking impending doom directly in Stremio.",
    "resources": ["catalog"],
    "types": ["movie"],
    "catalogs": [
        {"id": "horror_radar", "type": "movie", "name": "Incoming Horror"}
    ],
    "idPrefixes": ["tt"] # Tells Stremio we are feeding it IMDb IDs
}

@app.get("/manifest.json")
def get_manifest():
    return MANIFEST

@app.get("/catalog/movie/horror_radar.json")
def get_catalog():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/discover/movie"
    params = {
        "api_key": API_KEY,
        "with_genres": "27", 
        "primary_release_date.gte": today,
        "sort_by": "primary_release_date.asc",
        "region": "GB"
    }
    
    response = requests.get(url, params=params).json()
    results = response.get("results", [])[:15]
    
    metas = []
    for movie in results:
        tmdb_id = movie["id"]
        # The secondary interrogation to get the IMDb ID Stremio craves
        id_req = requests.get(f"{BASE_URL}/movie/{tmdb_id}/external_ids?api_key={API_KEY}").json()
        imdb_id = id_req.get("imdb_id")
        
        if imdb_id:
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
            
            metas.append({
                "id": imdb_id,
                "type": "movie",
                "name": movie.get("title"),
                "poster": poster_url,
                "description": movie.get("overview", "No description. Probably a terrible movie.")
            })
            
    return {"metas": metas}