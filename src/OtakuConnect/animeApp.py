import streamlit as st
from PIL import Image
import pandas as pd

#Import modules
from modules.anime_page import anime, anime_details
from modules.manga_page import manga, manga_details
from modules.community_page import community
from modules.recommender_page import recommender
from modules.auth_page import signup, login
from db_utils import get_connection, load_table_as_df 


if __name__ == '__main__':

    #session lable for various operations set to home by default
    if 'operation' not in st.session_state:
        st.session_state.operation = "home"

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False


    #opening connection to dp
    engine = get_connection('postgres', 'Rutgers123', 'localhost', 5401, 'OtakuConnectDB')

    #anime data
    anime_df = load_table_as_df(engine, 'anime')

    #manga data
    manga_df = load_table_as_df(engine, 'manga')

    #user data
    user_df =  load_table_as_df(engine, 'users')

    #list of genres
    genres_list = ["Action", "Adventure", "Comedy", "Drama", "Fantasy", "Slice of Life", "Horror",
    "Mystery", "Romance", "Sci-Fi", "Supernatural", "Thriller", "Sports", "Historical",
    "Music", "Psychological", "Mecha", "Seinen", "Shoujo", "Shounen", "Gore", "Parody", 
    "School", "Childcare","Super Power", "Reincarnation", "Military"]   

    genres_list.sort()

    st.set_page_config(page_title="OtakuConnect", page_icon="images/anime_background.jpeg") # For browser tab icon

    with st.sidebar:
        image = Image.open("images/anime_background.jpeg")
        st.image(image, use_column_width=True)

        if not st.session_state.logged_in:
            st.title(':red[Welcome to OtakuConnect] 🚀')
            if st.button("Home 🏠", type='primary', use_container_width=True):
                st.session_state.operation = "home"

            if st.button("Log in", type='primary', use_container_width=True):
                st.session_state.operation = "login"
                user_df = load_table_as_df(engine, 'users')

            if st.button("Sign Up", type='primary', use_container_width=True):
                st.session_state.operation = "signup"

        else:
            st.title(':red[OtakuConnect] 🚀')
            st.subheader(f':red[Hi] {st.session_state.username} 🤩')
            if st.button("Home 🏠", type='primary', use_container_width=True):
                st.session_state.operation = "home"

            if st.button("Anime 🎬", type='primary', use_container_width=True):
                st.session_state.operation = "anime"

            if st.button("Manga 📖", type='primary', use_container_width=True):
                st.session_state.operation = "manga"

            if st.button("Community 👫", type='primary', use_container_width=True):
                st.session_state.operation = "community"

            if st.button("Shuffle for Me 🕵️‍♀️", type='primary', use_container_width=True):
                st.session_state.operation = "recommender"

            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.operation = "home"
                st.rerun()


    
    if st.session_state.operation == "home":
        # 🏠 Greeting
        if st.session_state.get("logged_in") and st.session_state.get("username"):
            st.title(f':red[Welcome back, {st.session_state.username} 👋]')
        else:
            st.title(":red[Hello Reader, Hajimemashite 👋]")

        # 🔍 Search box
        search_term = st.text_input("Search Anime or Manga by Name").strip()

        # Convert dates safely
        anime_df['start_date'] = pd.to_datetime(anime_df['start_date'], errors='coerce')
        manga_df['start_date'] = pd.to_datetime(manga_df['start_date'], errors='coerce')
        today = pd.Timestamp.today()

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
            margin-bottom: 10px; 
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

        items_per_row = 3

        # --- If user entered a search term ---
        if search_term:
            st.subheader(f"🔍 Search Results for '{search_term}'")

            # Filter both anime & manga by title (case-insensitive)
            search_anime = anime_df[anime_df['title'].str.contains(search_term, case=False, na=False)]
            search_manga = manga_df[manga_df['title'].str.contains(search_term, case=False, na=False)]

            if search_anime.empty and search_manga.empty:
                st.info("No matching Anime or Manga found.")
            else:
                if not search_anime.empty:
                    st.markdown("### 🎬 Matching Animes")
                    for i in range(0, len(search_anime), items_per_row):
                        row = search_anime.iloc[i:i + items_per_row]
                        cols = st.columns(items_per_row)
                        for col, (_, anime_row) in zip(cols, row.iterrows()):
                            with col:
                                if pd.notna(anime_row["main_picture"]) and str(anime_row["main_picture"]).strip():
                                    st.markdown(
                                        f'<img class="anime-img" src="{anime_row["main_picture"]}" alt="{anime_row["title"]}">',
                                        unsafe_allow_html=True
                                    )
                                if st.button(anime_row["title"], key=f"anime_search_{anime_row['title']}", use_container_width=True):
                                    st.session_state.selected_anime = anime_row["title"]
                                    st.session_state.operation = "anime_details"
                                    st.rerun()

                if not search_manga.empty:
                    st.markdown("### 📖 Matching Mangas")
                    for i in range(0, len(search_manga), items_per_row):
                        row = search_manga.iloc[i:i + items_per_row]
                        cols = st.columns(items_per_row)
                        for col, (_, manga_row) in zip(cols, row.iterrows()):
                            with col:
                                if pd.notna(manga_row["main_picture"]) and str(manga_row["main_picture"]).strip():
                                    st.markdown(
                                        f'<img class="manga-img" src="{manga_row["main_picture"]}" alt="{manga_row["title"]}">',
                                        unsafe_allow_html=True
                                    )
                                if st.button(manga_row["title"], key=f"manga_search_{manga_row['title']}", use_container_width=True):
                                    st.session_state.selected_manga = manga_row["title"]
                                    st.session_state.operation = "manga_details"
                                    st.rerun()

        # --- Otherwise, show latest releases ---
        else:
            # Latest Anime (released within last 2 months)
            latest_anime = anime_df[
                (anime_df['start_date'] > today - pd.DateOffset(months=2)) &
                (anime_df['start_date'] <= today)
            ][['title', 'main_picture']].dropna(subset=['main_picture'])
            latest_anime = latest_anime[latest_anime['main_picture'].apply(lambda x: isinstance(x, str) and x.strip() != '')]

            # Latest Manga (released within last 12 months)
            latest_manga = manga_df[
                (manga_df['start_date'] > today - pd.DateOffset(months=12)) &
                (manga_df['start_date'] <= today)
            ][['title', 'main_picture']].dropna(subset=['main_picture'])
            latest_manga = latest_manga[latest_manga['main_picture'].apply(lambda x: isinstance(x, str) and x.strip() != '')]

            st.subheader(":red[Latest Animes]")
            for i in range(0, len(latest_anime), items_per_row):
                row = latest_anime.iloc[i:i + items_per_row]
                cols = st.columns(items_per_row)
                for col, (_, anime_row) in zip(cols, row.iterrows()):
                    with col:
                        if pd.notna(anime_row["main_picture"]) and str(anime_row["main_picture"]).strip():
                            st.markdown(
                                f'<img class="anime-img" src="{anime_row["main_picture"]}" alt="{anime_row["title"]}">',
                                unsafe_allow_html=True
                            )
                        if st.button(anime_row["title"], key=f"anime_{anime_row['title']}", use_container_width=True):
                            st.session_state.selected_anime = anime_row["title"]
                            st.session_state.operation = "anime_details"
                            st.rerun()

            st.subheader(":red[Latest Mangas]")
            for i in range(0, len(latest_manga), items_per_row):
                row = latest_manga.iloc[i:i + items_per_row]
                cols = st.columns(items_per_row)
                for col, (_, manga_row) in zip(cols, row.iterrows()):
                    with col:
                        if pd.notna(manga_row["main_picture"]) and str(manga_row["main_picture"]).strip():
                            st.markdown(
                                f'<img class="manga-img" src="{manga_row["main_picture"]}" alt="{manga_row["title"]}">',
                                unsafe_allow_html=True
                            )
                        if st.button(manga_row["title"], key=f"manga_{manga_row['title']}", use_container_width=True):
                            st.session_state.selected_manga = manga_row["title"]
                            st.session_state.operation = "manga_details"
                            st.rerun()


       
    elif st.session_state.operation == 'anime':
        anime(anime_df)

    elif st.session_state.operation == 'anime_details':
        anime_details(anime_df, engine)

    elif st.session_state.operation == 'manga':
        manga(manga_df)

    elif st.session_state.operation == 'manga_details':
        manga_details(manga_df, engine)

    elif st.session_state.operation == 'community':
        community()

    elif st.session_state.operation == 'recommender':
        if st.session_state.logged_in:
            recommender()
        else:
            st.warning("Please log in to use Shuffle For Me.")
            if st.button("Login Now"):
                st.session_state.operation = "login"
                st.rerun()

    elif st.session_state.operation == 'login':
        login(engine)

    elif st.session_state.operation == 'signup':
        signup(engine, user_df, genres_list)


    


        


     



