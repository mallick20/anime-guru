import streamlit as st

def recommender():
    st.title(":red[OUR RECOMMENDATION]")
    st.write("Recommendation system output goes here.")


def shuffle_recommender(user_preferences, user_history, user_feedback):
    """
    Function to get the content for the recommender page.
    Inputs:
        List of user preferences
        List of user history
        List of user comments, ratings, likes, dislikes
    Returns:
        Recommended content for the user based on their preferences and history.
    """

    
