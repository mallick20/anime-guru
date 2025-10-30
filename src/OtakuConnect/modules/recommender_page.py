import streamlit as st
import pandas as pd
from openai import AzureOpenAI

from db_utils import get_connection
from .config import *

# Initialize Azure OpenAI Client
openai_client = AzureOpenAI(
    azure_endpoint=azure_openai_endpoint,
    api_key=azure_openai_api_key,
    api_version=azure_openai_api_version
)

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

    if feedback_df.empty:
        return []

    # Divide the feeddback into two tables - anime feedback and manga feedback
    anime_feedback_df = feedback_df[feedback_df['entitytype'] == 'Anime']
    manga_feedback_df = feedback_df[feedback_df['entitytype'] == 'Manga']

    # Get the details of the respective anime and manga from the respective tables and join with the feedback data
    anime_ids = anime_feedback_df['entityid'].tolist()
    anime_details_df = pd.read_sql("SELECT id, title, rank, popularity, genres from anime where id in ({})".format(','.join(map(str, anime_ids+[]))), con=engine)  
    anime_feedback_df = anime_feedback_df.merge(anime_details_df, left_on='entityid', right_on='id', how='left')

    manga_ids = manga_feedback_df['entityid'].tolist()
    manga_details_df = pd.read_sql("SELECT id, title, rank, popularity, genres from manga where id in ({})".format(','.join(map(str, manga_ids+[]))), con=engine)  
    manga_feedback_df = manga_feedback_df.merge(manga_details_df, left_on='entityid', right_on='id', how='left')


    # Remerge the two feedback dataframes
    feedback_df = pd.concat([anime_feedback_df, manga_feedback_df], ignore_index=True)

    # Sort and give the latest feedback (last month)
    feedback_df = feedback_df.sort_values(by='reviewdate', ascending=False)
    today = pd.Timestamp.today()
    feedback_df['daydiff'] = (today - feedback_df['reviewdate']).dt.days

    feedback_df = feedback_df[feedback_df['daydiff'] <= 30]

    # Required columns
    feedback_df = feedback_df[['entitytype','title', 'reviewcontent', 'genres']]

    # List
    feedback_list = feedback_df.to_dict(orient='records')

    # Drop some unnecessary columns
    return feedback_list

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
    preferences_df = pd.read_sql("SELECT favoritegenres from users where id={}".format(user_id), con=engine)
    preferences_list = preferences_df['favoritegenres'].iloc[0].split(',')

    return preferences_list


def get_user_history(user_id = None):
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

    prompt_text = '''
    Given the user preferences: {}, user history: {}, and user feedback: {}, generate a list of recommended anime and manga titles. 
    The recommendations should be diverse and align with the user's interests while avoiding titles they have already engaged with. 
    Give top 5 recommendations only.
    
    Provide the recommendations in a JSON format with the following structure:
    {{
        "recommendations": [
            {{
                "title": "Title 1",
                "type": "anime/manga",
                "genre": "Genre 1",
                "reason": "Reason for recommendation"
            }},
            {{
                "title": "Title 2",
                "type": "anime/manga",
                "genre": "Genre 2",
                "reason": "Reason for recommendation"
            }},
            ...
        ]
    }}


    '''
    
    messages = [
        {"role": "system", "content": "You are a helpful AI that recommends anime and manga based on user preferences, history, and feedback."
        "Always respond in the specified JSON format."},
        {"role": "user", "content": prompt_text},
    ]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1024,
        temperature=0
    )

    return response.choices[0].message['content']

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
