import streamlit as st
from PIL import Image
import pandas as pd

#Import modules
from modules.anime_page import anime, anime_details
from modules.manga_page import manga, manga_details
from modules.community_page import community
from modules.recommender_page import recommender
from db_utils import get_connection, load_table_as_df 

if __name__ == '__main__':

    #session lable for various operations set to home by default
    if 'operation' not in st.session_state:
        st.session_state.operation = "home"

    #opening connection to dp
    engine = get_connection('postgres', 'Rutgers123', 'localhost', 5401, 'OtakuConnectDB')

    #anime data
    anime_df = load_table_as_df(engine, 'anime')
    anime_df = anime_df.drop(columns='id')

    #manga data
    manga_df = load_table_as_df(engine, 'manga')
    manga_df = manga_df.drop(columns='id')

    st.set_page_config(page_title="OtakuConnect", page_icon="images/anime_background.jpeg") # For browser tab icon

    with st.sidebar:
        image = Image.open("images/anime_background.jpeg")
        st.image(image, use_column_width=True)
        st.title(':red[Welcome to OtakuConnect] 🚀')

        if st.button("Home :house_with_garden:", type='primary',use_container_width=True):
            st.session_state.operation = "home"

        if st.button("Anime :movie_camera:", type='primary', use_container_width=True):
            st.session_state.operation = "anime"

        if st.button("Manga :closed_book:", type="primary", use_container_width=True):
            st.session_state.operation = "manga"
        
        if st.button("Community 👫", type="primary", use_container_width=True):
            st.session_state.operation = "community"

        if st.button("Shuffle For Me 🕵️‍♀️", type='primary', use_container_width=True):
            st.session_state.operation = "recommender"
       
        my_container = st.container()
        
        with my_container:
            col1, col2 = st.columns([1,2])

            with col1:
                if st.button("Log in", use_container_width=True):
                    st.write('login')
            
            with col2:
                if st.button("Sign Up", use_container_width=True):
                    st.write('hello')


    
    if st.session_state.operation == "home":
        st.title(":red[Hello Reader, Hajimemashite]")

        search_term = st.text_input("Search Anime or Manga by Name")
        if search_term:
            st.write(f"Search Results for {search_term}")

        # Convert dates safely
        anime_df['start_date'] = pd.to_datetime(anime_df['start_date'], errors='coerce')
        anime_df['end_date'] = pd.to_datetime(anime_df['end_date'], errors='coerce')
        manga_df['start_date'] = pd.to_datetime(manga_df['start_date'], errors='coerce')
        manga_df['end_date'] = pd.to_datetime(manga_df['end_date'], errors='coerce')

        today = pd.Timestamp.today()

        # --- Latest Anime (released within last 2 months) ---
        latest_anime = anime_df[(anime_df['start_date'] > today - pd.DateOffset(months=2)) & (anime_df['start_date'] <= today)][['title', 'main_picture']]

        latest_anime = latest_anime.dropna(subset=['main_picture'])
        latest_anime = latest_anime[latest_anime['main_picture'].apply(lambda x: isinstance(x, str) and x.strip() != '')]

        # --- Latest Manga (released within last 12 months) ---
        latest_manga = manga_df[(manga_df['start_date'] > today - pd.DateOffset(months=12)) &(manga_df['start_date'] <= today)][['title', 'main_picture']]
        latest_manga = latest_manga.dropna(subset=['main_picture'])
        latest_manga = latest_manga[latest_manga['main_picture'].apply(lambda x: isinstance(x, str) and x.strip() != '')]

        # --- Shared CSS for uniform look ---
        st.markdown("""
        <style>
        .anime-img, .manga-img {
            width: 100%;
            height: 300px;
            object-fit: cover;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            transition: transform 0.2s ease;
            margin-bottom: 10px; /* 👈 space between image & title */
        }
        .anime-img:hover, .manga-img:hover {
            transform: scale(1.03);
        }
        .anime-title, .manga-title {
            text-align: center;
            font-weight: 600;
            font-size: 1rem;
            color: #e63946;
            margin-top: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

        # --- Display Latest Animes ---
        st.subheader(":red[Latest Animes]")
        items_per_row = 3

        for i in range(0, len(latest_anime), items_per_row):
            row = latest_anime.iloc[i:i + items_per_row]
            cols = st.columns(items_per_row)

            for col, (_, anime_row) in zip(cols, row.iterrows()):
                with col:
                    try:
                        st.markdown(
                            f'<img class="anime-img" src="{anime_row["main_picture"]}" alt="{anime_row["title"]}">',
                            unsafe_allow_html=True
                        )
                        
                        if st.button(anime_row["title"], key=f"anime_{anime_row['title']}", use_container_width=True):
                            st.session_state.selected_anime = anime_row["title"]
                            st.session_state.operation = "anime_details"
                    except Exception as e:
                        print(f"Skipping anime {anime_row['title']}: {e}")
                        continue

        # --- Display Latest Mangas ---
        st.write('\n')
        st.subheader(":red[Latest Mangas]")

        for i in range(0, len(latest_manga), items_per_row):
            row = latest_manga.iloc[i:i + items_per_row]
            cols = st.columns(items_per_row)

            for col, (_, manga_row) in zip(cols, row.iterrows()):
                with col:
                    try:
                        st.markdown(
                            f'<img class="manga-img" src="{manga_row["main_picture"]}" alt="{manga_row["title"]}">',
                            unsafe_allow_html=True
                        )
                        if st.button(manga_row["title"],key=f"manga_{manga_row['title']}", use_container_width=True):
                            st.session_state.selected_manga = manga_row["title"]
                            st.session_state.operation = "manga_details"
                    except Exception as e:
                        print(f"Skipping manga {manga_row['title']}: {e}")
                        continue

       
    elif st.session_state.operation == 'anime':
        anime(anime_df)

    elif st.session_state.operation == 'anime_details':
        anime_details(anime_df)

    elif st.session_state.operation == 'manga':
        manga(manga_df)

    elif st.session_state.operation == 'manga_details':
        manga_details(manga_df)

    elif st.session_state.operation == 'community':
        community()

    elif st.session_state.operation == 'recommender':
        recommender()


    


        


     



