from sqlalchemy import text
from datetime import datetime
import streamlit as st
import pandas as pd
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

def manga(manga_df):
    st.title(":red[MANGAS]")

    items_per_row = 3
    items_per_load = 15

    # Initialize visible manga count
    if "visible_manga" not in st.session_state:
        st.session_state.visible_manga = items_per_load

    def reset_visible():
        st.session_state.visible_manga = items_per_load

    # ---- SEARCH ----
    search_term = st.text_input("Search Manga by Name", on_change=reset_visible).strip()

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
            {g.strip() for sub in manga_df["genres"].dropna() for g in sub.split(",")}
        )

        selected_genres = col2.multiselect(
            "Filter by Genre",
            all_genres,
            on_change=reset_visible
        )

    # ---- APPLY SEARCH ----
    if search_term:
        manga_list = manga_df[manga_df["title"].str.contains(search_term, case=False, na=False)]
        st.subheader(f"🔍 Search Results for '{search_term}'")
    else:
        manga_list = manga_df.copy()

        # ✔ Apply genre filters only when NOT searching
        if selected_genres:
            manga_list = manga_list[
                manga_list["genres"]
                .fillna("")
                .apply(lambda x: all(g in x for g in selected_genres))
            ]

    # ---- APPLY SORTING ----
    if sort_by == "Latest" and "start_date" in manga_list.columns:
        manga_list = manga_list.sort_values(by="start_date", ascending=False)

    elif sort_by == "Oldest" and "start_date" in manga_list.columns:
        manga_list = manga_list.sort_values(by="start_date", ascending=True)

    elif sort_by == "Highest Rating" and "rating" in manga_list.columns:
        manga_list = manga_list.sort_values(by="rating", ascending=False)

    elif sort_by == "Lowest Rating":
        if "mean" in manga_list.columns:
            manga_list["mean_numeric"] = (
                pd.to_numeric(manga_list["mean"], errors="coerce").fillna(0)
            )
            manga_list = manga_list.sort_values(by="mean_numeric", ascending=True)

    elif sort_by == "A → Z":
        manga_list = manga_list.sort_values(by="title", ascending=True)

    elif sort_by == "Z → A":
        manga_list = manga_list.sort_values(by="title", ascending=False)

    # If nothing left
    if manga_list.empty:
        st.info("No manga match your filters or search.")
        return

    # ---- PAGINATION ----
    visible_df = manga_list.iloc[:st.session_state.visible_manga]

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
        st.markdown(
            "<h3 style='text-align: center;'>One Stop Destination To All Your Favourite Mangas</h3>",
            unsafe_allow_html=True
        )

        for i in range(0, len(visible_df), items_per_row):
            row = visible_df.iloc[i:i + items_per_row]
            cols = st.columns(items_per_row)

            for col, (_, manga_row) in zip(cols, row.iterrows()):
                with col:

                    # Image
                    if pd.notna(manga_row["main_picture"]) and str(manga_row["main_picture"]).strip():
                        st.markdown(
                            f'<img class="manga-img" src="{manga_row["main_picture"]}" alt="{manga_row["title"]}">',
                            unsafe_allow_html=True
                        )

                    # Button
                    if st.button(
                        manga_row["title"],
                        key=f"manga_{int(manga_row['id'])}",
                        use_container_width=True
                    ):
                        st.session_state.selected_manga = manga_row["title"]
                        st.session_state.operation = "manga_details"
                        st.rerun()

        # ---- LOAD MORE ----
        if st.session_state.visible_manga < len(manga_list):
            st.button(
                "⬇ Load More",
                type="primary",
                on_click=lambda: st.session_state.update(
                    {"visible_manga": st.session_state.visible_manga + items_per_load}
                )
            )



def manga_details(manga_df, engine, log_user_activity):
    title = st.session_state.get("selected_manga", None)
    
    if not title:
        st.warning("No manga selected.")
        return

    data = manga_df[manga_df['title'] == title]

    if data.empty:
        st.error("Manga not found in the database.")
        return

    manga_id = int(data['id'].iloc[0])

    # ------------------- Display Manga Details -------------------
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
        col1, col2 = st.columns([1,2])
        with col1:
            if pd.notna(data['main_picture'].iloc[0]):
                st.image(data['main_picture'].iloc[0], caption=data['title'].iloc[0])
        with col2:
            st.markdown(f"<span style='color:#BBB8FF'>Synopsis:</span> {data['synopsis'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Status:</span> {data['status'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Published On:</span> {data['start_date'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Rating:</span> {data['mean'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Popularity:</span> {data['popularity'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Genres:</span> {data['genres'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Total Volumes:</span> {data['num_volumes'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Authors:</span> {data['authors'].iloc[0]}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#BBB8FF'>Media Type:</span> {data['media_type'].iloc[0]}", unsafe_allow_html=True)

    # ------------------- Log View Activity -------------------
    if st.session_state.get("logged_in"):
        log_user_activity(
            engine,
            st.session_state.user_id,
            manga_id,
            entitytype_id=2,      # 2 = Manga
            activitytype_id=1,    # 1 = Viewed
            content=f"Viewed details of {title}"
        )

    st.divider()

    # ------------------- Feedback Section -------------------
    if st.session_state.get("logged_in", False):
        st.subheader("⭐ Rate and Review this Manga")

        with st.form("manga_feedback_form", clear_on_submit=True):
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
                                VALUES (:rating, :userid, 'Manga', :entityid, :reviewtitle, :reviewcontent, :spoilerflag, :reviewdate, 'Pending')
                            """),
                            {
                                "rating": int(rating),
                                "userid": int(st.session_state.user_id),
                                "entityid": int(manga_id),
                                "reviewtitle": auto_title,
                                "reviewcontent": review_content.strip(),
                                "spoilerflag": bool(spoiler_flag),
                                "reviewdate": datetime.now()
                            }
                        )

                    # log rating activity
                    log_user_activity(
                        engine,
                        st.session_state.user_id,
                        manga_id,
                        entitytype_id=2,      # 2 = Manga
                        activitytype_id=2,    # 2 = Rated
                        content=f"Rated {rating}/10 for {title}"
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

    # ------------------- Display Existing Community Feedback -------------------
    st.subheader("💬 Community Feedback")

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT f.reviewtitle, f.reviewcontent, f.rating, f.reviewdate, 
                           f.spoilerflag, u.username
                    FROM feedback_table f
                    JOIN users u ON f.userid = u.id
                    WHERE f.entitytype = 'Manga'
                      AND f.entityid = :entityid
                      AND f.moderatedstatus = 'Approved'
                    ORDER BY f.reviewdate DESC
                """),
                {"entityid": manga_id}
            ).fetchall()

        if rows:
            for row in rows:
                mapping = getattr(row, "_mapping", None)
                rtitle = mapping.get('reviewtitle') if mapping else row['reviewtitle']
                rcontent = mapping.get('reviewcontent') if mapping else row['reviewcontent']
                rrating = mapping.get('rating') if mapping else row['rating']
                rdate = mapping.get('reviewdate') if mapping else row['reviewdate']
                ruser = mapping.get('username') if mapping else row['username']
                rspoiler = mapping.get('spoilerflag') if mapping else row['spoilerflag']

                st.markdown(f"**{rtitle}** — ⭐ {rrating}/10")
                if rspoiler:
                    with st.expander("⚠️ Spoiler — click to reveal"):
                        st.write(rcontent)
                else:
                    st.write(rcontent)
                st.caption(f"— by {ruser} on {rdate.strftime('%b %d, %Y')}")
                st.divider()
        else:
            st.info("No approved feedback yet. Be the first to review this manga!")
    except Exception as e:
        st.error(f"Error loading feedback: {e}")
