import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time

# Constants for readability
ENTITY_TYPES = {
    "ANIME": 1,
    "MANGA": 2
}

ACTIVITY_TYPES = {
    "VIEWED": 1,
    "RATED": 2,
    "COMMENTED": 3
}


def anime(anime_df):
    st.title(":red[ANIMES]")
    st.write("One Stop Destination To All Your Favourite Animes")
    items_per_row = 3
    
    search_term = st.text_input("Search Anime by Name").strip()
    if search_term:
        st.subheader(f"🔍 Search Results for '{search_term}'")
        search_anime = anime_df[anime_df['title'].str.contains(search_term, case=False, na=False)]

        if search_anime.empty:
            st.info("No matching Anime found.")
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
                        st.rerun()
                except Exception as e:
                    print(f"Skipping anime {anime_row['title']}: {e}")
                    continue



def anime_details(anime_df, engine, log_user_activity):
    title = st.session_state.get("selected_anime", None)
    if not title:
        st.warning("No anime selected.")
        return

    data = anime_df[anime_df['title'] == title]
    if data.empty:
        st.error("Anime not found in local dataframe.")
        return

    anime_id = int(data['id'].iloc[0])

    # --- Display Anime Details ---
    st.title(f":red[{title}]")

    my_container = st.container()

    with my_container:
        col1, col2 = st.columns([1, 2])
        with col1:
            if pd.notna(data['main_picture'].iloc[0]):
                st.image(data['main_picture'].iloc[0], caption=data['title'].iloc[0])
        with col2:
            st.markdown(f"<span style='color:#BBB8FF'>Synopsis:</span> {data['synopsis'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Status:</span> {data['status'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Aired On:</span> {data['start_date'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Rating:</span> {data['mean'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Views:</span> {data['popularity'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Genres:</span> {data['genres'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Agerating:</span> {str(data['agerating'].iloc[0]).upper()}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Studio:</span> {data['studios'].iloc[0]}", unsafe_allow_html=True)

    # --- Log "Viewed" Activity Once Per Session ---
    if st.session_state.get("logged_in"):
        log_user_activity(
            engine,
            st.session_state.user_id,
            anime_id,
            ENTITY_TYPES["ANIME"],
            ACTIVITY_TYPES["VIEWED"],
            f"Viewed details of {title}"
        )
        st.session_state.view_logged = True

    st.divider()

    # --- Feedback Form (for logged-in users) ---
    if st.session_state.get("logged_in", False):
        st.subheader("⭐ Rate and Review this Anime")

        with st.form("feedback_form", clear_on_submit=True):
            rating = st.slider("Your Rating", 1, 10, 8)
            review_content = st.text_area("Your Review (no spoilers please)")
            spoiler_flag = st.checkbox("Contains Spoilers?")
            submit = st.form_submit_button("Submit Feedback")

        if submit:
            if not review_content.strip():
                st.warning("Please write your review before submitting.")
            else:
                auto_title = f"Review for {title}"
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO feedback_table
                                (rating, userid, entitytype, entityid, reviewtitle, reviewcontent, spoilerflag, reviewdate, moderatedstatus)
                                VALUES (:rating, :userid, 'Anime', :entityid, :reviewtitle, :reviewcontent, :spoilerflag, :reviewdate, 'Pending')
                            """),
                            {
                                "rating": int(rating),
                                "userid": int(st.session_state.user_id),
                                "entityid": int(anime_id),
                                "reviewtitle": auto_title,
                                "reviewcontent": review_content.strip(),
                                "spoilerflag": bool(spoiler_flag),
                                "reviewdate": datetime.now()
                            }
                        )

                        # Log user rating activity
                        log_user_activity(
                            engine,
                            st.session_state.user_id,
                            anime_id,
                            ENTITY_TYPES["ANIME"],
                            ACTIVITY_TYPES["RATED"],
                            f"Rated {rating}/10 for {title}"
                        )

                    st.success("✅ Feedback submitted! It will be visible once approved.")
                    st.toast("Your feedback was saved!", icon="🔥")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving feedback: {e}")
    else:
        st.info("🔒 Please log in to submit feedback or comment.")

    st.divider()

    # --- Display Approved Community Feedback ---
    st.subheader("💬 Community Feedback")
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT f.reviewtitle, f.reviewcontent, f.rating, f.reviewdate, f.spoilerflag, u.username
                    FROM feedback_table f
                    JOIN users u ON f.userid = u.id
                    WHERE f.entitytype = 'Anime'
                    AND f.entityid = :entityid
                    AND f.moderatedstatus = 'Approved'
                    ORDER BY f.reviewdate DESC
                """),
                {"entityid": anime_id}
            ).fetchall()

        if rows:
            st.caption(f"📢 {len(rows)} approved community review(s) for this anime.")
            for row in rows:
                mapping = getattr(row, "_mapping", None)
                if mapping:
                    rtitle = mapping.get("reviewtitle")
                    rcontent = mapping.get("reviewcontent")
                    rrating = mapping.get("rating")
                    rdate = mapping.get("reviewdate")
                    rauthor = mapping.get("username")
                    spoilerflag = mapping.get("spoilerflag")
                else:
                    rtitle = row["reviewtitle"]
                    rcontent = row["reviewcontent"]
                    rrating = row["rating"]
                    rdate = row["reviewdate"]
                    rauthor = row["username"]
                    spoilerflag = row["spoilerflag"]

                st.markdown(f"### {rtitle} — ⭐ {rrating}/10")

                # 👇 spoiler-aware rendering
                if spoilerflag:
                    with st.expander("⚠️ Spoiler Review — Click to Reveal"):
                        st.write(rcontent)
                else:
                    st.write(rcontent)

                st.caption(f"— by {rauthor} on {rdate.strftime('%b %d, %Y')}")
                st.divider()
        else:
            st.info("No approved feedback yet. Be the first to review this anime!")

    except Exception as e:
        st.error(f"Error loading feedback: {e}")
