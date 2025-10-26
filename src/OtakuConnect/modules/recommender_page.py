import streamlit as st
import pandas as pd

from db_utils import get_connection
from config import username, password, host, port, db_name


def get_user_feedback(user_id = None):
    """
    Function to get user feedback from the recommender page.
    Inputs:
        None
    Returns:
        User feedback data.
    """
    
    engine = get_connection(username, password, host, port, db_name)

    # Get the user feedback data from the database
    feedback_df = pd.read_sql("SELECT * from feedback_table where userid={}".format(user_id), con=engine)

    # Divide the feeddback into two tables - anime feedback and manga feedback
    anime_feedback_df = feedback_df[feedback_df['entitytype'] == 'anime']
    manga_feedback_df = feedback_df[feedback_df['entitytype'] == 'manga']

    # Get the details of the respective anime and manga from the respective tables and join with the feedback data
    anime_ids = anime_feedback_df['entityid'].tolist()
    anime_details_df = pd.read_sql("SELECT id , rank, popularity, genres from anime where id in ({})".format(','.join(map(str, anime_ids))), con=engine)  
    anime_feedback_df = anime_feedback_df.merge(anime_details_df, left_on='entityid', right_on='id', how='left')

    manga_ids = manga_feedback_df['entityid'].tolist()
    manga_details_df = pd.read_sql("SELECT id, rank, popularity, genres from manga where id in ({})".format(','.join(map(str, manga_ids))), con=engine)  
    manga_feedback_df = manga_feedback_df.merge(manga_details_df, left_on='entityid', right_on='id', how='left')


    # Remerge the two feedback dataframes
    feedback_df = pd.concat([anime_feedback_df, manga_feedback_df], ignore_index=True)

    # Sort and give the latest feedback (last month)
    feedback_df = feedback_df.sort_values(by='reviewdate', ascending=False)
    today = pd.Timestamp.today()
    feedback_df['daydiff'] = (today - feedback_df['reviewdate']).dt.days

    feedback_df = feedback_df[feedback_df['daydiff'] <= 30]

    # Drop some unnecessary columns
    return feedback_df

def get_user_preferences(user_id = None):
    """
    Function to get user preferences from the recommender page.
    Inputs:
        User ID
    Returns:
        User preferences data.
    """

    engine = get_connection(username, password, host, port, db_name)

    # Get the user preferences data from the database
    preferences_df = pd.read_sql("SELECT favoritegenres from users where userid={}".format(user_id), con=engine)
    preferences_list = preferences_df['favoritegenres'].iloc[0].split(',')

    return preferences_list


def get_user_history():
    """
    Function to get user history from the recommender page.
    Inputs:
        User ID
    Returns:
        User history data.
    """

    return []


def shuffle_recommender(user_preferences, user_history, user_feedback):
    """
    Function to get the content for the recommender page.
    Inputs:
        List of user preferences
        List of user history
        List of user feedback
    Returns:
        Recommended content for the user based on their preferences and history.
    """

    pass

def recommender():
    st.title(":red[OUR RECOMMENDATION]")
    st.write("Recommendation system output goes here.")

    user_id = st.session_state.get("user_id", None)
    if user_id is None:
        st.info("🔒 Please log in to see personalized recommendations.")
        return
    
    user_feedback = get_user_feedback(user_id)
    user_preferences = get_user_preferences(user_id)
    user_history = get_user_history(user_id)

    recommended_content = shuffle_recommender(user_preferences, user_history, user_feedback)
