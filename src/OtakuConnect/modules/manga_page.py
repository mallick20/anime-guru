import streamlit as st
import pandas as pd

def manga(manga_df):
    st.title(":red[MANGAS]")

    st.write("One Stop Destination To All Your Favourite Mangas")
    
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
    
    items_per_row = 3
    for i in range(0, len(manga_df), items_per_row):
            row = manga_df.iloc[i:i + items_per_row]
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


def manga_details(manga_df):
    title = st.session_state.get("selected_manga", None)
    
    if not title:
        st.warning("No manga selected.")
        return

    data = manga_df[manga_df['title'] == title]
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
            st.markdown(f"<span style='color:#BBB8FF'>Total Volumes:</span> {data['num_volumes'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Authors:</span> {data['authors'].iloc[0]}",unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Media Type:</span> {data['media_type'].iloc[0]}",unsafe_allow_html=True)
    
    st.write(":green[Would you like the rate this manga, please star based on your experience.]")

    feedback_mapping = [1,2,3,4,5]
    selected = st.feedback("stars")
    if selected is not None:
        st.markdown(f"You selected {feedback_mapping[selected]} star(s).")
        st.toast("Your feedback was saved!", icon="🔥")

    