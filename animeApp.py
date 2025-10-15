import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import re


def anime():
    pass

def manga():
    pass

def community():
    pass

def recommender():
    pass


if __name__ == '__main__':

    if 'operation' not in st.session_state:
        st.session_state.operation = "home"

    st.set_page_config(page_title="OtakuConnect", page_icon="/Users/dikshaphuloria/Desktop/anime_background.jpeg") # For browser tab icon

    with st.sidebar:
        image = Image.open("/Users/dikshaphuloria/Desktop/anime_background.jpeg")
        st.image(image, use_column_width=True)
        st.title(':red[Welcome to OtakuConnect] 🚀')

        if st.button("Home :house_with_garden:", type='primary',use_container_width=True):
            st.session_state.operation = "home"

        if st.button("Anime :movie_camera:", type='primary', use_container_width=True):
            st.session_state.operation = "anime"

        if st.button("Manga :closed_book:", type="primary", use_container_width=True):
            st.session_state.operation = "manga"
        
        if st.button("Community 👫", type="primary", use_container_width=True):
            st.session_state.opertion = "community"

        if st.button("Shuffle For Me 🕵️‍♀️", type='primary', use_container_width=True):
            st.session_state.opertion = "recommender"


    
    if st.session_state.operation == "home":
        # Display an image within the app
        st.title(":green[Hello Reader, Hajimemashite]")
        


    elif st.session_state.operation == 'anime':
        anime()


    elif st.session_state.operation == 'manga':
        manga()


    elif st.session_state.operation == 'community':
        community()


    elif st.session_state.operation == 'recommender':
        recommender()


    


        


     



