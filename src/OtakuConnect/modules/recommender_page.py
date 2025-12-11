import streamlit as st
import time
import random
from sqlalchemy import text
from modules.user_log import log_user_activity
import json
import re
import pandas as pd
from openai import AzureOpenAI

# Import config
from config import Config

def parse_query(message):
    """Parse user message into structured JSON"""
    try:
        system_prompt = """You are a specialized query parser for an anime/manga recommendation system. 
        Your task is to analyze user requests and extract their preferences into a structured JSON format.
        You must respond ONLY with valid JSON - no explanations, no markdown formatting, no additional text."""
        
        user_prompt = """Parse the following user request into a JSON object:

                User message: "{message}"

                Required JSON structure:
                {{
                    "top_rated": boolean (true if user wants highly rated/best content),
                    "latest": boolean (true if user wants newest/recent/latest releases),
                    "watch_history_consideration": boolean (true if user mentions "similar", "like what I watched", "based on my history"),
                    "genre_considered": [list of genre strings - extract any mentioned: action, comedy, romance, thriller, sci-fi, fantasy, horror, adventure, supernatural, historical, slice-of-life, sports, mystery],
                    "type_preference": string ("Anime", "Manga", or "Anime" if not specified),
                    "number_of_recommendations": integer (extract number from request, default to 5 if not mentioned),
                    "status_preference": string ("ongoing", "completed", or "any" if not specified),
                    "year_preference": integer or null (specific year mentioned, e.g., "from 2015" -> 2015, "after 2020" -> 2020),
                    "years_back": integer or null (relative time period mentioned, e.g., "last 5 years" -> 5, "past decade" -> 10, "recent 3 years" -> 3)
                }}

                Important rules:
                - If a field is not mentioned, use sensible defaults
                - Extract genres carefully - user might say "funny" (comedy), "scary" (horror), etc.
                - For top_rated: look for keywords like "best", "top", "highest rated", "popular"
                - For watch_history: look for "similar to", "like", "based on what I've watched"

                Return ONLY the JSON object, nothing else."""
        
        client = AzureOpenAI(
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT, 
            api_key=Config.AZURE_OPENAI_API_KEY, 
            api_version=Config.AZURE_OPENAI_API_VERSION,
        )
        formatted_user_prompt = user_prompt.format(message=message)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        parsed_json = json.loads(response.choices[0].message.content)
        return parsed_json
    
    except Exception as e:
        print(f"OpenAI API error: {e}, falling back to rule-based parsing")
    
    # Rule-based parsing (fallback)
    lower_msg = message.lower()

    genres = ['action', 'comedy', 'romance', 'thriller', 'sci-fi', 'fantasy', 
            'horror', 'adventure', 'supernatural', 'historical', 'slice-of-life', 
            'sports', 'mystery']
    genre_considered = [g for g in genres if g in lower_msg]

    number_match = re.search(r'\b(\d+)\b', message)
    number_of_recommendations = int(number_match.group(1)) if number_match else 5

    year_match = re.search(r'\b(19|20)\d{2}\b', message)
    year_preference = int(year_match.group()) if year_match else None

    years_back = None
    years_back_patterns = [
        (r'last\s+(\d+)\s+years?', lambda m: int(m.group(1))),
        (r'past\s+(\d+)\s+years?', lambda m: int(m.group(1))),
        (r'recent\s+(\d+)\s+years?', lambda m: int(m.group(1))),
        (r'past\s+decade', lambda m: 10),
        (r'last\s+decade', lambda m: 10),
    ]

    for pattern, extractor in years_back_patterns:
        match = re.search(pattern, lower_msg)
        if match:
            years_back = extractor(match)
            break

    latest_keywords = ['latest', 'newest', 'new', 'recent', 'current', 'this year', 'this season']
    latest = any(keyword in lower_msg for keyword in latest_keywords)

    if 'recent' in lower_msg and not years_back:
        latest = True

    return {
        "top_rated": any(word in lower_msg for word in ['top', 'best', 'highest rated', 'popular', 'must-watch', 'must watch']),
        "latest": latest,
        "watch_history_consideration": any(word in lower_msg for word in ['like', 'similar', 'based on', 'like what i', 'similar to']),
        "genre_considered": genre_considered,
        "type_preference": 'manga' if 'manga' in lower_msg else ('anime' if 'anime' in lower_msg else 'both'),
        "number_of_recommendations": number_of_recommendations,
        "status_preference": 'ongoing' if 'ongoing' in lower_msg else ('completed' if 'completed' in lower_msg else 'any'),
        "year_preference": year_preference,
        "years_back": years_back
    }

def get_anime_recommendations(user_message, user_id=3, engine=None):

    feedback_raw = pd.read_sql("SELECT * FROM FEEDBACK_TABLE", engine)
    user_feedback = feedback_raw[feedback_raw["userid"] == user_id]
    liked_entities = user_feedback[user_feedback["rating"] >= 8]
    liked_anime_ids = set(liked_entities[liked_entities["entitytype"] == "Anime"]["entityid"].tolist())
    liked_manga_ids = set(liked_entities[liked_entities["entitytype"] == "Manga"]["entityid"].tolist())
    
    parsed_query = parse_query(user_message)
    print(f"parsed_query:{parsed_query}")
    conditions = []
    table = "anime"
    order_by = []
    
    if parsed_query['type_preference'].lower() == 'manga':
        table = "manga"
        
    if parsed_query['genre_considered']:
        genre_conditions = ' OR '.join([f"genres ILIKE '%{g}%'" for g in parsed_query['genre_considered']])
        conditions.append(f"({genre_conditions})")
    
    if parsed_query['watch_history_consideration']:
        liked = liked_anime_ids if table == "anime" else liked_manga_ids
        if liked:
            history_genre_conditions = ' OR '.join([f"genres ILIKE '%{g}%'" for g in liked])
            conditions.append(f"({history_genre_conditions})")
    
    if parsed_query['status_preference'] == 'ongoing':
        if table == "anime":
            conditions.append(f"status = 'currently_airing'")
        else:
            conditions.append(f"status = 'currently_publishing'")
    elif parsed_query['status_preference'] == 'completed':
        if table == "anime":
            conditions.append(f"status = 'finished_airing'")
        else:
            conditions.append(f"status = 'finished'")
    
    if parsed_query['year_preference']:
        conditions.append(f"EXTRACT(YEAR FROM start_date) >= {parsed_query['year_preference']}")
        
    if parsed_query['years_back']:
        conditions.append(f"EXTRACT(YEAR FROM start_date) >= (EXTRACT(YEAR FROM CURRENT_DATE) - {parsed_query['years_back']})")
    
    if parsed_query['top_rated']:
        order_by.append("rank ASC")
        
    if parsed_query['latest']:
        order_by.append("start_date DESC")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    ordering = "ORDER BY " + ", ".join(order_by) if order_by else ""
    
    sql_query = f"""
        SELECT id, title, genres, synopsis, main_picture, mean, popularity, status, 
        EXTRACT(YEAR FROM start_date) as year,
        {f"num_episodes, studios" if table == "anime" else "num_volumes, num_chapters, authors"}
        FROM {table}
        {where_clause}
        {ordering}
        LIMIT {parsed_query['number_of_recommendations']}
    """
    sql_query = sql_query.strip()
    print("sql_query:", sql_query[:500] if isinstance(sql_query, str) else sql_query)
    
    results = pd.read_sql(text(sql_query), engine)
        
    return {
        "response": results,
        "media_type": "Anime" if table == "anime" else "Manga",
        "debug_info": {
            "parsed_query": parsed_query,
            "sql_query": sql_query.strip(),
            "result_count": len(results)
        }
    }


def display_recommendations_grid(recommendations, media_type, source="shuffle"):
    """Reusable function to display recommendations in a grid format"""
    if len(recommendations) == 0:
        st.warning(f"No {media_type.lower()} found matching your criteria.")
        return
    
    media_icon = "🎬" if media_type == "Anime" else "📖"
    st.markdown(f"### {media_icon} Your Personalized {media_type} Recommendations")
    
    for idx, (_, item) in enumerate(recommendations.iterrows(), 1):
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if item.get('main_picture'):
                    st.image(item['main_picture'])
                else:
                    st.info("No image available")
            
            with col2:
                st.markdown(f"### {idx}. {item['title']}")
                
                # Metrics based on media type
                if media_type == "Anime":
                    badge_col1, badge_col2, badge_col3 = st.columns(3)
                    with badge_col1:
                        st.metric("⭐ Rating", f"{item['mean']:.1f}" if pd.notna(item.get('mean')) else "N/A")
                    with badge_col2:
                        st.metric("👁 Popularity", f"#{int(item['popularity'])}" if pd.notna(item.get('popularity')) else "N/A")
                    with badge_col3:
                        st.metric("📺 Episodes", int(item.get('num_episodes', 0)) if pd.notna(item.get('num_episodes')) else "N/A")
                else:
                    badge_col1, badge_col2, badge_col3 = st.columns(3)
                    with badge_col1:
                        st.metric("⭐ Rating", f"{item['mean']:.1f}" if pd.notna(item.get('mean')) else "N/A")
                    with badge_col2:
                        st.metric("👁 Popularity", f"#{int(item['popularity'])}" if pd.notna(item.get('popularity')) else "N/A")
                    with badge_col3:
                        volumes = int(item.get('num_volumes', 0)) if pd.notna(item.get('num_volumes')) else 'N/A'
                        chapters = int(item.get('num_chapters', 0)) if pd.notna(item.get('num_chapters')) else 'N/A'
                        st.metric("📚 Vol/Ch", f"{volumes}/{chapters}")
                
                # Genres
                if item.get('genres'):
                    genres_list = [g.strip() for g in str(item['genres']).split(',')][:5]
                    st.write("**Genres:**", " • ".join(genres_list))
                
                # Status and additional info
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    if item.get('status'):
                        st.write(f"**Status:** {item['status']}")
                with info_col2:
                    if media_type == "Anime" and item.get('studios'):
                        studios = str(item['studios']).split(',')[0]
                        st.write(f"**Studio:** {studios}")
                    elif media_type == "Manga" and item.get('authors'):
                        authors = str(item['authors']).split(',')[0]
                        st.write(f"**Author:** {authors}")
                
                # Synopsis preview
                if item.get('synopsis'):
                    synopsis = str(item['synopsis'])
                    preview = synopsis[:200] + "..." if len(synopsis) > 200 else synopsis
                    st.write(preview)
                
                # View details button
                button_key = f"detail_{source}_{item['title']}_{idx}"
                if media_type == "Anime":
                    if st.button(f"📖 View Full Details", key=button_key, use_container_width=True):
                        st.session_state.selected_anime = item['title']
                        st.session_state.previous_operation = "recommender"
                        st.session_state.operation = "anime_details"
                        st.rerun()
                else:
                    if st.button(f"📖 View Full Details", key=button_key, use_container_width=True):
                        st.session_state.selected_manga = item['title']
                        st.session_state.previous_operation = "recommender"
                        st.session_state.operation = "manga_details"
                        st.rerun()


def shuffle_recommender(anime_df, manga_df, engine):
    """Original shuffle functionality extracted as separate function"""
    st.markdown("### 🎲 Random Discovery Mode")
    st.write("Get personalized recommendations based on your preferences and discovery style!")
    
    # Initialize session state
    if 'shuffle_recommendations' not in st.session_state:
        st.session_state.shuffle_recommendations = None
    if 'shuffling' not in st.session_state:
        st.session_state.shuffling = False
    if 'media_type' not in st.session_state:
        st.session_state.media_type = "Anime"

    # Get user's preferences
    user_genres = []
    user_id = None
    if st.session_state.get('logged_in') and st.session_state.get('username'):
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT id, favoritegenres FROM users WHERE username = :username"),
                {"username": st.session_state.username}
            ).fetchone()
            if result:
                user_id = result[0]
                if result[1]:
                    if isinstance(result[1], str):
                        user_genres = [g.strip() for g in result[1].split(',')]
                    else:
                        user_genres = result[1]
    
    # Recommendation settings
    with st.expander("🎯 Customize Your Shuffle", expanded=True):
        selected_media_type = st.radio(
            "What do you want to discover?",
            ["Anime", "Manga"],
            horizontal=True,
            help="Choose between Anime or Manga recommendations"
        )

        if selected_media_type != st.session_state.media_type:
            st.session_state.media_type = selected_media_type
            st.session_state.shuffle_recommendations = None
            st.session_state.shuffling = False
            st.rerun()
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            rec_type = st.radio(
                "Recommendation Type",
                ["Based on My Preferences", "Popular Picks", "Hidden Gems", "Random Discovery"],
                help="Choose how you want to discover content"
            )
        
        with col2:
            num_recommendations = st.slider(
                "Number of Recommendations",
                min_value=3,
                max_value=10,
                value=5,
                help="How many items to show"
            )
            
            min_rating = st.slider(
                "Minimum Rating",
                min_value=5.0,
                max_value=10.0,
                value=7.5,
                step=0.5,
                help="Filter by minimum rating"
            )

    # Shuffle button
    if st.button("🔀 SHUFFLE FOR ME", type='primary', use_container_width=True, key="shuffle_btn"):
        st.session_state.shuffling = True
        st.rerun()
    
    # Shuffling animation
    if st.session_state.shuffling:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        statuses = [
            ("🔍 Scanning the database...", 20),
            ("🎭 Analyzing your taste...", 40),
            ("🎨 Finding the perfect matches...", 60),
            ("✨ Polishing recommendations...", 80),
            ("🎉 Almost ready...", 90),
        ]
        
        for status, progress in statuses:
            status_text.write(status)
            progress_bar.progress(progress)
            time.sleep(0.3)
        
        progress_bar.progress(100)
        status_text.write("🎊 Ready!")
        time.sleep(0.2)
        
        selected_df = anime_df if st.session_state.media_type == "Anime" else manga_df
        filtered_items = selected_df[selected_df['mean'] >= min_rating].copy()
        
        if rec_type == "Based on My Preferences" and user_genres:
            def has_matching_genre(genres_str):
                if not genres_str or genres_str == '' or genres_str is None:
                    return False
                genre_list = [g.strip() for g in str(genres_str).split(',')]
                return any(user_genre in genre_list for user_genre in user_genres)
            
            filtered_items = filtered_items[filtered_items['genres'].apply(has_matching_genre)]
            
            if len(filtered_items) == 0:
                st.warning(f"No {st.session_state.media_type.lower()} found matching your genre preferences. Showing popular picks instead!")
                filtered_items = selected_df[selected_df['mean'] >= min_rating].copy()
                filtered_items = filtered_items.sort_values('popularity', ascending=True)
        
        elif rec_type == "Popular Picks":
            filtered_items = filtered_items.sort_values('popularity', ascending=True)
        
        elif rec_type == "Hidden Gems":
            filtered_items = filtered_items[filtered_items['popularity'] > 1000]
            filtered_items = filtered_items.sort_values('mean', ascending=False)
        
        if len(filtered_items) > 0:
            sample_size = min(num_recommendations, len(filtered_items))
            st.session_state.shuffle_recommendations = filtered_items.sample(n=sample_size)
            
            if user_id and st.session_state.get('logged_in'):
                try:
                    first_item_id = st.session_state.shuffle_recommendations.iloc[0]['id']
                    entity_type = 1 if st.session_state.media_type == "Anime" else 2
                    log_user_activity(
                        engine=engine,
                        user_id=user_id,
                        entity_id=first_item_id,
                        entity_type=entity_type,
                        activity_type=6,
                        content=f"Received {sample_size} {rec_type} {st.session_state.media_type.lower()} recommendations"
                    )
                except Exception as e:
                    pass
        else:
            st.session_state.shuffle_recommendations = None
        
        st.session_state.shuffling = False
        progress_bar.empty()
        status_text.empty()
        st.rerun()
    
    # Display recommendations
    if st.session_state.shuffle_recommendations is not None:
        st.markdown("---")
        display_recommendations_grid(
            st.session_state.shuffle_recommendations, 
            st.session_state.media_type,
            source="shuffle"
        )
    else:
        st.info("👆 Click the **SHUFFLE FOR ME** button to get personalized recommendations!")


def chatbot_recommender(anime_df, manga_df, engine):
    """AI-powered natural language recommendation system"""
    st.markdown("### 💬 Smart Recommendation Assistant")
    st.write("Describe what you're looking for in natural language, and I'll find the perfect match!")
    
    # Initialize session state
    if 'chatbot_recommendations' not in st.session_state:
        st.session_state.chatbot_recommendations = None
    if 'chatbot_processing' not in st.session_state:
        st.session_state.chatbot_processing = False
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ""
    if 'chatbot_fallback' not in st.session_state:
        st.session_state.chatbot_fallback = False
    
    # Get user ID
    user_id = None
    if st.session_state.get('logged_in') and st.session_state.get('username'):
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": st.session_state.username}
            ).fetchone()
            if result:
                user_id = result[0]
    
    # Example queries
    with st.expander("💡 Example Queries", expanded=False):
        st.markdown("""
        Try asking things like:
        - "Show me 5 action anime from the last 3 years"
        - "I want top-rated romance manga"
        - "Give me sci-fi anime similar to what I've watched"
        - "Show me the best comedy anime"
        - "Find me ongoing thriller manga from 2020"
        - "I need hidden gem fantasy anime"
        """)
    
    # Text input
    user_message = st.text_area(
        "🎯 What are you looking for?",
        placeholder="e.g., 'I want 5 action anime from the past 3 years with high ratings'",
        height=100,
        key="chatbot_input"
    )
    
    # Search button
    if st.button("🔍 Find Recommendations", type='primary', use_container_width=True, key="chatbot_search"):
        if user_message.strip():
            st.session_state.user_query = user_message
            st.session_state.chatbot_processing = True
            st.session_state.chatbot_fallback = False
            st.rerun()
        else:
            st.warning("Please describe what you're looking for!")
    
    # Processing animation and recommendation logic
    if st.session_state.chatbot_processing:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        statuses = [
            ("🤖 Understanding your request...", 20),
            ("🔎 Searching the database...", 50),
            ("🎯 Finding the best matches...", 80),
        ]
        
        for status, progress in statuses:
            status_text.write(status)
            progress_bar.progress(progress)
            time.sleep(0.3)
        
        progress_bar.progress(100)
        status_text.write("✅ Found results!")
        time.sleep(0.2)
        
        # Get recommendations using the chatbot function
        try:
            result = get_anime_recommendations(
                st.session_state.user_query, 
                user_id=user_id if user_id else 3, 
                engine=engine
            )
            
            recommendations = result["response"]
            media_type = result["media_type"]
            
            # Check if results are empty
            if len(recommendations) == 0:
                st.session_state.chatbot_fallback = True
                # Generate fallback recommendations using shuffle logic
                st.warning("⚠️ No exact matches found for your request. Here are some popular recommendations instead!")
                
                selected_df = anime_df if media_type == "Anime" else manga_df
                filtered_items = selected_df[selected_df['mean'] >= 7.5].copy()
                filtered_items = filtered_items.sort_values('popularity', ascending=True)
                
                sample_size = min(5, len(filtered_items))
                recommendations = filtered_items.head(sample_size)
            
            st.session_state.chatbot_recommendations = recommendations
            st.session_state.chatbot_media_type = media_type
            
            # Log activity
            if user_id and st.session_state.get('logged_in') and len(recommendations) > 0:
                try:
                    first_item_id = recommendations.iloc[0]['id']
                    entity_type = 1 if media_type == "Anime" else 2
                    log_user_activity(
                        engine=engine,
                        user_id=user_id,
                        entity_id=first_item_id,
                        entity_type=entity_type,
                        activity_type=6,
                        content=f"Chatbot query: {st.session_state.user_query[:100]}"
                    )
                except Exception as e:
                    pass
        
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.session_state.chatbot_recommendations = None
        
        st.session_state.chatbot_processing = False
        progress_bar.empty()
        status_text.empty()
        st.rerun()
    
    # Display results
    if st.session_state.chatbot_recommendations is not None:
        st.markdown("---")
        
        if st.session_state.chatbot_fallback:
            st.info("💡 Showing popular recommendations since we couldn't find exact matches. Try refining your search!")
        else:
            st.success(f"✨ Found {len(st.session_state.chatbot_recommendations)} recommendations based on your query!")
        
        display_recommendations_grid(
            st.session_state.chatbot_recommendations,
            st.session_state.chatbot_media_type,
            source="chatbot"
        )
        
        # Option to try again
        if st.button("🔄 Try Another Search", use_container_width=True):
            st.session_state.chatbot_recommendations = None
            st.session_state.user_query = ""
            st.session_state.chatbot_fallback = False
            st.rerun()
    else:
        st.info("👆 Describe what you're looking for and click **Find Recommendations**!")


def recommender(anime_df, manga_df, engine):
    """Main recommender page with mode selection"""
    st.title(":red[🎯 ANIME & MANGA RECOMMENDER]")
    
    # Initialize mode in session state
    if 'recommender_mode' not in st.session_state:
        st.session_state.recommender_mode = None
    
    # Show mode selection if no mode is chosen
    if st.session_state.recommender_mode is None:
        st.markdown("---")
        st.markdown("### Choose Your Discovery Style")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("### 🎲 Shuffle For Me")
                st.write("**Quick & Fun Random Discovery**")
                if st.button("🎲 Start Shuffling", use_container_width=True, type="primary", key="select_shuffle"):
                    st.session_state.recommender_mode = "shuffle"
                    st.rerun()
        
        with col2:
            with st.container(border=True):
                st.markdown("### 💬 Smart Assistant")
                st.write("**AI-Powered Natural Language Search**")
                if st.button("💬 Chat with Assistant", use_container_width=True, type="primary", key="select_chatbot"):
                    st.session_state.recommender_mode = "chatbot"
                    st.rerun()
        
        # Quick stats
        st.markdown("---")
        st.markdown("### 📊 Database Stats")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Anime", f"{len(anime_df):,}")
        with col2:
            st.metric("Total Manga", f"{len(manga_df):,}")
        with col3:
            avg_anime_rating = anime_df['mean'].mean()
            st.metric("Avg Anime Rating", f"{avg_anime_rating:.1f}")
        with col4:
            avg_manga_rating = manga_df['mean'].mean()
            st.metric("Avg Manga Rating", f"{avg_manga_rating:.1f}")
    
    else:
        # Show back button
        if st.button("⬅️ Back to Mode Selection", key="back_to_modes"):
            st.session_state.recommender_mode = None
            # Clear any stored recommendations
            if 'shuffle_recommendations' in st.session_state:
                st.session_state.shuffle_recommendations = None
            if 'chatbot_recommendations' in st.session_state:
                st.session_state.chatbot_recommendations = None
            st.rerun()
        
        st.markdown("---")
        
        # Route to appropriate recommender
        if st.session_state.recommender_mode == "shuffle":
            shuffle_recommender(anime_df, manga_df, engine)
        elif st.session_state.recommender_mode == "chatbot":
            chatbot_recommender(anime_df, manga_df, engine)