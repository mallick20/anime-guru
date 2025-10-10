import streamlit as st
import pandas as pd
import time

def anime(anime_df):
    st.title(":red[ANIMES]")
    st.write("One Stop Destination To All Your Favourite Animes")

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
    items_per_row = 3

    for i in range(0, len(anime_df), items_per_row):
        row = anime_df.iloc[i:i + items_per_row]
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


def anime_details(anime_df):
    title = st.session_state.get("selected_anime", None)
    
    if not title:
        st.warning("No anime selected.")
        return

    data = anime_df[anime_df['title'] == title]

    st.title(f':red[{title}]')

    my_container = st.container()

    with my_container:
        col1, col2 = st.columns([1,2])

        with col1:
            st.image(data['main_picture'].iloc[0], caption=data['title'].iloc[0])

        with col2:
            st.markdown(f"<span style='color:#BBB8FF'>Synopsis:</span> {data['synopsis'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Status:</span> {data['status'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Aired On:</span> {data['start_date'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Rating:</span> {data['mean'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Views:</span> {data['popularity'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Genres:</span> {data['genres'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Agerating:</span> {data['agerating'].iloc[0].upper()}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Studio:</span> {data['studios'].iloc[0]}",unsafe_allow_html=True)
    
    st.write(":red[Would you like the rate this anime, please star based on your experience.]")

    feedback_mapping = [1,2,3,4,5]
    selected = st.feedback("stars")
    if selected is not None:
        st.markdown(f"You selected {feedback_mapping[selected]} star(s).")
        st.toast("Your feedback was saved!", icon="🔥")

        
        


    


