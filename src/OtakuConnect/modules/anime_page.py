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

    items_per_row = 3
    items_per_load = 15

    # Initialize visible anime count
    if "visible_anime" not in st.session_state:
        st.session_state.visible_anime = items_per_load

    def reset_visible():
        st.session_state.visible_anime = items_per_load

    # ---- SEARCH ----
    search_term = st.text_input("Search Anime by Name", on_change=reset_visible).strip()

    # ---- FILTERS ----
    with st.expander("🔎 Apply Filters", expanded=False):
        col1, col2 = st.columns(2)

        sort_by = col1.selectbox(
            "Sort By",
            [
                "Default",
                "Latest",
                "Oldest",
                "Highest Rating",
                "Lowest Rating",
                "A → Z",
                "Z → A",
            ],
            on_change=reset_visible
        )

        all_genres = sorted(
            {g.strip() for sub in anime_df["genres"].dropna() for g in sub.split(",")}
        )

        selected_genres = col2.multiselect(
            "Filter by Genre",
            all_genres,
            on_change=reset_visible
        )

    # ---- APPLY SEARCH ----
    if search_term:
        anime_list = anime_df[anime_df["title"].str.contains(search_term, case=False, na=False)]
        st.subheader(f"🔍 Search Results for '{search_term}'")

    else:
        anime_list = anime_df.copy()

        if selected_genres:
            anime_list = anime_list[
                anime_list["genres"]
                .fillna("")
                .apply(lambda x: all(g in x for g in selected_genres))
            ]

    # ---- APPLY SORTING ----
    if sort_by == "Latest" and "start_date" in anime_list.columns:
        anime_list = anime_list.sort_values(by="start_date", ascending=False)

    elif sort_by == "Oldest" and "start_date" in anime_list.columns:
        anime_list = anime_list.sort_values(by="start_date", ascending=True)

    elif sort_by == "Highest Rating" and "rating" in anime_list.columns:
        anime_list = anime_list.sort_values(by="rating", ascending=False)

    elif sort_by == "Lowest Rating":
        if "mean" in anime_list.columns:
            anime_list["mean_numeric"] = (
                pd.to_numeric(anime_list["mean"], errors="coerce").fillna(0)
            )
            anime_list = anime_list.sort_values(by="mean_numeric", ascending=True)

    elif sort_by == "A → Z":
        anime_list = anime_list.sort_values(by="title", ascending=True)

    elif sort_by == "Z → A":
        anime_list = anime_list.sort_values(by="title", ascending=False)

    # If nothing left
    if anime_list.empty:
        st.info("No anime match your filters or search.")
        return

    # ---- PAGINATION ----
    visible_df = anime_list.iloc[:st.session_state.visible_anime]

    # ---- CSS ----
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
        </style>
    """, unsafe_allow_html=True)

    # ---- DISPLAY ----
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>One Stop Destination To All Your Favourite Animes</h3>", unsafe_allow_html=True)

        for i in range(0, len(visible_df), items_per_row):
            row = visible_df.iloc[i:i + items_per_row]
            cols = st.columns(items_per_row)

            for col, (_, anime_row) in zip(cols, row.iterrows()):
                with col:

                    # Image
                    if pd.notna(anime_row["main_picture"]) and str(anime_row["main_picture"]).strip():
                        st.markdown(
                            f'<img class="anime-img" src="{anime_row["main_picture"]}" alt="{anime_row["title"]}">',
                            unsafe_allow_html=True
                        )

                    # Button (stable ID key)
                    if st.button(
                        anime_row["title"],
                        key=f"anime_{int(anime_row['id'])}",
                        use_container_width=True
                    ):
                        st.session_state.selected_anime = anime_row["title"]
                        st.session_state.operation = "anime_details"
                        st.rerun()

        # ---- LOAD MORE ----
        if st.session_state.visible_anime < len(anime_list):
            st.button(
                "⬇ Load More",
                type="primary",
                on_click=lambda: st.session_state.update(
                    {"visible_anime": st.session_state.visible_anime + items_per_load}
                )
            )



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
    if st.session_state.get('previous_operation') == 'recommender':
        if st.button("⬅️ Back To Recommendations", type='primary'):
            st.session_state.operation = "recommender"
            st.session_state.previous_operation = None
            st.rerun()
        st.markdown("---")

    else:
        if st.button(":arrow_left: Return To Home", type='primary'):
            st.session_state.operation = "home"
            st.rerun()

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
