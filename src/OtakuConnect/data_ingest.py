import requests
import time
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

from config import Config
from db_utils import get_connection, load_table_as_df


CLIENT_ID = Config.CLIENT_ID

#opening connection to dp
engine = get_connection(Config.DB_USERNAME,
                        Config.DB_PASSWORD,
                        Config.DB_HOST,
                        Config.DB_PORT,
                        Config.DB_NAME)

ANIMEBASE_URL = "https://api.myanimelist.net/v2/anime/ranking"
ANIME_FIELDS = "id,title,main_picture,mean,rank,popularity,status,genres,num_episodes,duration,rating,studios,start_date,end_date,synopsis"

MANGABASE_URL = "https://api.myanimelist.net/v2/manga/ranking"
MANGA_FIELDS = "id,title,authors{first_name,last_name},main_picture,mean,rank,popularity,status,genres,num_pages,num_volumes,num_chapters,media_type,start_date,end_date,synopsis"

def fix_date(date):
    try:
        # Try to convert to datetime
        return pd.to_datetime(date, errors="raise").date()
    except:
        # If conversion fails, check if it's a year-only string
        if isinstance(date, str) and date.isdigit() and len(date) == 4:
            return pd.to_datetime(f"{date}-01-01").date()
        else:
            return None  # or pd.NaT
        
def get_anime_data(total=2000, limit=100):
    anime_list = []
    for offset in range(0, total, limit):
        params = {
            "ranking_type": "all",   # get top ranked anime
            "limit": limit,
            "offset": offset,
            "fields": ANIME_FIELDS
        }
        headers = {"X-MAL-CLIENT-ID": CLIENT_ID}

        response = requests.get(ANIMEBASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            break

        data = response.json()
        anime_list.extend([entry["node"] for entry in data["data"]])

        print(f"Fetched {len(anime_list)} anime so far...")
        time.sleep(1)  

    print(f"\n✅ Done! Collected {len(anime_list)} anime entries.")

    animedf=pd.DataFrame(anime_list)
    animedf['genres'] = animedf['genres'].apply(lambda g: ", ".join(d['name'] for d in g) if isinstance(g, list) else None)
    animedf['main_picture']=animedf['main_picture'].apply(lambda x: x['medium'])
    animedf['studios']=animedf['studios'].apply(lambda g: ", ".join(d['name'] for d in g) if isinstance(g, list) else None)
    animedf= animedf.rename(columns={'rating': 'agerating'})
    animedf["start_date"] = animedf["start_date"].apply(fix_date)
    animedf["end_date"] = animedf["end_date"].apply(fix_date)
    
    return animedf


def get_manga_data(total=2000, limit=100):
    manga_list = []
    for offset in range(0, total, limit):
        params = {
            "ranking_type": "all",  
            "limit": limit,
            "offset": offset,
            "fields": MANGA_FIELDS
        }
        headers = {"X-MAL-CLIENT-ID": CLIENT_ID}

        response = requests.get(MANGABASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            break

        data = response.json()
        manga_list.extend([entry["node"] for entry in data["data"]])

        print(f"Fetched {len(manga_list)} manga so far...")
        time.sleep(1)   

    print(f"\n✅ Done! Collected {len(manga_list)} manga entries.")

    mangadf = pd.DataFrame(manga_list)

    mangadf["authors"] = mangadf["authors"].apply(lambda a: ", ".join([f"{d['node']['first_name']} {d['node']['last_name']}" for d in a]) if isinstance(a, list) else None)
    mangadf['genres'] = mangadf['genres'].apply(lambda g: ", ".join(d['name'] for d in g) if isinstance(g, list) else None)
    mangadf['main_picture']=mangadf['main_picture'].apply(lambda x: x['medium'])
    mangadf["start_date"] = mangadf["start_date"].apply(fix_date)
    mangadf["end_date"] = mangadf["end_date"].apply(fix_date)
    
    return mangadf






if __name__ == "__main__":
    print("Data ingestion pipeline")

    # Read existing data
    existing_animedf = pd.read_sql("SELECT title FROM anime", con=engine)
    existing_mangadf = pd.read_sql("SELECT title FROM manga", con=engine)

    #animedf = animedf.drop(columns=["id"])
    #mangadf = mangadf.drop(columns=["id"])

    animedf = get_anime_data(total=2000, limit=100)
    mangadf = get_manga_data(total=2000, limit=100)

    # Filter out rows already in DB
    animedf = animedf[~animedf["title"].isin(existing_animedf["title"])]
    mangadf = mangadf[~mangadf["title"].isin(existing_mangadf["title"])]

    #Reordering the columns Anime
    animedb_columns = ['title', 'main_picture', 'mean', 'rank', 'popularity', 'status',
        'genres', 'num_episodes', 'start_date', 'end_date', 'synopsis',
        'agerating', 'studios']
        
    animedf = animedf[animedb_columns]

    #Reordering the columns Manga
    mangadb_columns = ['title', 'main_picture', 'authors', 'mean', 'rank', 'popularity',
        'status', 'genres', 'num_volumes', 'num_chapters', 'media_type',
        'start_date', 'end_date', 'synopsis']
    mangadf = mangadf[mangadb_columns]

    #Dumping data to DB
    animedf.to_sql("anime", con=engine, if_exists="append", index=False)
    mangadf.to_sql("manga", con=engine, if_exists="append", index=False)