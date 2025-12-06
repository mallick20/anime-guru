import streamlit as st
import time
import random
from sqlalchemy import text
from modules.user_log import log_user_activity

def recommender(anime_df, manga_df, engine):
    st.title(":red[🎲 SHUFFLE FOR ME]")
        
    # Initialize session state for recommendations
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    if 'shuffling' not in st.session_state:
        st.session_state.shuffling = False
    if 'media_type' not in st.session_state:
        st.session_state.media_type = "Anime"

    # Get user's preferences if logged in
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
                    # Handle both string and list formats
                    if isinstance(result[1], str):
                        user_genres = [g.strip() for g in result[1].split(',')]
                    else:
                        user_genres = result[1]
    
    # Recommendation settings
    with st.expander("🎯 Customize Your Shuffle", expanded=False):
        # Media type selection
        selected_media_type = st.radio(
            "What do you want to discover?",
            ["Anime", "Manga"],
            horizontal=True,
            help="Choose between Anime or Manga recommendations"
        )

        # Detect media type change
        if selected_media_type != st.session_state.media_type:
            st.session_state.media_type = selected_media_type
            st.session_state.recommendations = None      # ← CLEAR old results
            st.session_state.shuffling = False           # ← optional but cleaner
            st.rerun() 
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            rec_type = st.radio(
                "Recommendation Type",
                ["Based on My Preferences", "Popular Picks", "Hidden Gems", "Random Discovery"],
                help="Choose how you want to discover anime"
            )
        
        with col2:
            num_recommendations = st.slider(
                "Number of Recommendations",
                min_value=3,
                max_value=10,
                value=10,
                help="How many anime to show"
            )
            
            min_rating = st.slider(
                "Minimum Rating",
                min_value=5.0,
                max_value=10,
                value=7.5,
                step=0.5,
                help="Filter by minimum rating"
            )
    if st.session_state.media_type == "Anime":
            st.markdown("### 🎬 **Currently Browsing: Anime**")
    else:
        st.markdown("### 📖 **Currently Browsing: Manga**")

    # Shuffle button
    shuffle_placeholder = st.empty()
    
    with shuffle_placeholder.container():
        if st.button("🔀 SHUFFLE FOR ME", type='primary', use_container_width=True):
            st.session_state.shuffling = True
            st.rerun()
    
    # Shuffling animation
    if st.session_state.shuffling:
        shuffle_placeholder.empty()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Animation sequence
        statuses = [
            ("🔍 Scanning the anime database...", 20),
            ("🎭 Analyzing your taste...", 40),
            ("🎨 Finding the perfect matches...", 60),
            ("✨ Polishing recommendations...", 80),
            ("🎉 Almost ready...", 90),
        ]
        
        for status, progress in statuses:
            status_text.write(status)
            progress_bar.progress(progress)
            time.sleep(0.5)
        
        progress_bar.progress(100)
        status_text.write("🎊 Ready!")
        time.sleep(0.3)
        
        # Select the appropriate dataframe based on media type
        selected_df = anime_df if st.session_state.media_type == "Anime" else manga_df
        
        # Generate recommendations based on type
        filtered_items = selected_df[selected_df['mean'] >= min_rating].copy()
        
        if rec_type == "Based on My Preferences" and user_genres:
            # Filter by user's genre preferences
            def has_matching_genre(genres_str):
                if not genres_str or genres_str == '' or genres_str is None:
                    return False
                genre_list = [g.strip() for g in str(genres_str).split(',')]
                return any(user_genre in genre_list for user_genre in user_genres)
            
            filtered_items = filtered_items[filtered_items['genres'].apply(has_matching_genre)]
            
            # If no matches found, fall back to popular picks
            if len(filtered_items) == 0:
                st.warning(f"No {st.session_state.media_type.lower()} found matching your genre preferences. Showing popular picks instead!")
                filtered_items = selected_df[selected_df['mean'] >= min_rating].copy()
                filtered_items = filtered_items.sort_values('popularity', ascending=True)
        
        elif rec_type == "Popular Picks":
            # Sort by popularity (lower number = more popular)
            filtered_items = filtered_items.sort_values('popularity', ascending=True)
        
        elif rec_type == "Hidden Gems":
            # Higher popularity number (less popular) but high rating
            filtered_items = filtered_items[filtered_items['popularity'] > 1000]
            filtered_items = filtered_items.sort_values('mean', ascending=False)
        
        # Random Discovery uses the filtered list as-is
        
        # Select random recommendations
        if len(filtered_items) > 0:
            sample_size = min(num_recommendations, len(filtered_items))
            st.session_state.recommendations = filtered_items.sample(n=sample_size)
            
            # Log the recommendation activity
            if user_id and st.session_state.get('logged_in'):
                try:
                    # Get first recommended item ID to log
                    first_item_id = st.session_state.recommendations.iloc[0]['id']
                    entity_type = 1 if st.session_state.media_type == "Anime" else 2  # 1=Anime, 2=Manga
                    log_user_activity(
                        engine=engine,
                        user_id=user_id,
                        entity_id=first_item_id,
                        entity_type=entity_type,
                        activity_type=6,  # You may need to create an activity type for "Got Recommendations"
                        content=f"Received {sample_size} {rec_type} {st.session_state.media_type.lower()} recommendations"
                    )
                except Exception as e:
                    # Silently fail if logging doesn't work
                    pass
        else:
            st.session_state.recommendations = None
        
        st.session_state.shuffling = False
        progress_bar.empty()
        status_text.empty()
        st.rerun()
    
    # Display recommendations
    if st.session_state.recommendations is not None:
        st.markdown("---")
        media_icon = "🎬" if st.session_state.media_type == "Anime" else "📖"
        st.subheader(f"{media_icon} Your Personalized {st.session_state.media_type} Picks")
        
        recommendations = st.session_state.recommendations
        
        if len(recommendations) == 0:
            st.warning(f"No {st.session_state.media_type.lower()} found matching your criteria. Try adjusting the filters!")
        else:
            # Display in a grid
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
                        
                        # Determine which metrics to show based on media type
                        if st.session_state.media_type == "Anime":
                            # Rating and popularity badges for Anime
                            badge_col1, badge_col2, badge_col3 = st.columns(3)
                            with badge_col1:
                                st.metric("⭐ Rating", f"{item['mean']:.1f}" if item.get('mean') else "N/A")
                            with badge_col2:
                                st.metric("👁 Popularity", f"#{item['popularity']}" if item.get('popularity') else "N/A")
                            with badge_col3:
                                st.metric("📺 Episodes", item.get('num_episodes', 'N/A'))
                        else:
                            # Rating and popularity badges for Manga
                            badge_col1, badge_col2, badge_col3 = st.columns(3)
                            with badge_col1:
                                st.metric("⭐ Rating", f"{item['mean']:.1f}" if item.get('mean') else "N/A")
                            with badge_col2:
                                st.metric("👁 Popularity", f"#{item['popularity']}" if item.get('popularity') else "N/A")
                            with badge_col3:
                                volumes = item.get('num_volumes', 'N/A')
                                chapters = item.get('num_chapters', 'N/A')
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
                            if st.session_state.media_type == "Anime" and item.get('studios'):
                                studios = str(item['studios']).split(',')[0]  # Show first studio
                                st.write(f"**Studio:** {studios}")
                            elif st.session_state.media_type == "Manga" and item.get('authors'):
                                authors = str(item['authors']).split(',')[0]  # Show first author
                                st.write(f"**Author:** {authors}")
                        
                        # Synopsis preview
                        if item.get('synopsis'):
                            synopsis = str(item['synopsis'])
                            preview = synopsis[:200] + "..." if len(synopsis) > 200 else synopsis
                            st.write(preview)
                        
                        # View details button - different for anime vs manga
                        if st.session_state.media_type == "Anime":
                            if st.button(f"📖 View Full Details", key=f"detail_{item['title']}", use_container_width=True):
                                st.session_state.selected_anime = item['title']
                                st.session_state.previous_operation = "recommender"
                                st.session_state.operation = "anime_details"
                                st.rerun()
                        else:
                            if st.button(f"📖 View Full Details", key=f"detail_{item['title']}", use_container_width=True):
                                st.session_state.selected_manga = item['title']
                                st.session_state.previous_operation = "recommender"
                                st.session_state.operation = "manga_details"
                                st.rerun()

    else:
        # Welcome message when no recommendations yet
        st.info("👆 Click the **SHUFFLE FOR ME** button to get personalized recommendations!")
        
        # Show some stats
        if st.session_state.get('logged_in'):
            st.markdown("### 📊 Quick Stats")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Anime", len(anime_df))
            with col2:
                st.metric("Total Manga", len(manga_df))
            with col3:
                if user_genres:
                    st.metric("Your Preferred Genres", len(user_genres))
                else:
                    st.metric("Your Preferred Genres", 0)
            with col4:
                avg_rating = anime_df['mean'].mean()
                st.metric("Avg Anime Rating", f"{avg_rating:.1f}")