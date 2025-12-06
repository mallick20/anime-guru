import streamlit as st
from datetime import datetime
from sqlalchemy import text

def community(user_df, engine):
    tab1, tab2, tab3 = st.tabs(['Forum', 'Users', 'Latest Updates'])

    # ------------------ FORUM SECTION ------------------
    with tab1:
        st.header("Start Discussion Chain on Your Favourite Anime/Manga 🥳")

        # ---- Create New Discussion Thread ----
        if st.session_state.get("logged_in", False):
            with st.form("create_thread", clear_on_submit=True):
                thread_title = st.text_input("Start a discussion topic:")
                submit_thread = st.form_submit_button("Create Thread")

            if submit_thread:
                if thread_title.strip():
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    INSERT INTO discussion_threads (userid, title, created_at)
                                    VALUES (:userid, :title, :created_at)
                                """),
                                {
                                    "userid": st.session_state.user_id,
                                    "title": thread_title.strip(),
                                    "created_at": datetime.now()
                                }
                            )
                        st.success("✅ Discussion created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating discussion: {e}")
                else:
                    st.warning("Thread title cannot be empty.")
        else:
            st.info("🔐 Login to start a discussion thread.")

        st.divider()

        # ---- Display Existing Threads ----
        st.subheader("💬 Active Discussion Threads")

        try:
            with engine.connect() as conn:
                threads = conn.execute(
                    text("""
                        SELECT t.id, t.title, t.created_at, u.username
                        FROM discussion_threads t
                        JOIN users u ON t.userid = u.id
                        ORDER BY t.created_at DESC
                    """)
                ).fetchall()

            if threads:
                for thread in threads:
                    mapping = thread._mapping
                    thread_id = mapping["id"]
                    title = mapping["title"]
                    created = mapping["created_at"]
                    author = mapping["username"]
                    
                    with st.expander(f"🧵 {title} — by {author} on {created.strftime('%b %d, %Y')}"):   
                        st.header(f":violet[{title}]")
                        # Load replies
                        st.write(" ")
                        with engine.connect() as conn:
                            replies = conn.execute(
                                text("""
                                    SELECT r.reply, r.created_at, u.username
                                    FROM discussion_replies r
                                    JOIN users u ON r.userid = u.id
                                    WHERE r.threadid = :tid
                                    ORDER BY r.created_at ASC
                                """),
                                {"tid": thread_id}
                            ).fetchall()

                        # Show replies
                        if replies:
                            for rep in replies:
                                rm = rep._mapping
                                st.markdown(
                                    f"**{rm['username']}** · _{rm['created_at'].strftime('%b %d, %Y %H:%M')}_\n"
                                    f"{rm['reply']}"
                                )
                                st.divider()

                        # Add a reply
                        if st.session_state.get("logged_in", False):
                            with st.form(f"reply_form_{thread_id}", clear_on_submit=True):
                                reply_text = st.text_area("Reply to this thread")
                                send_reply = st.form_submit_button("Reply ▶")
                            
                            if send_reply:
                                if reply_text.strip():
                                    try:
                                        with engine.begin() as conn:
                                            conn.execute(
                                                text("""
                                                    INSERT INTO discussion_replies (threadid, userid, reply, created_at)
                                                    VALUES (:tid, :uid, :reply, :dt)
                                                """),
                                                {
                                                    "tid": thread_id,
                                                    "uid": st.session_state.user_id,
                                                    "reply": reply_text.strip(),
                                                    "dt": datetime.now()
                                                }
                                            )
                                        st.success("✅ Reply posted")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error posting reply: {e}")
                                else:
                                    st.warning("Reply cannot be empty.")
                        else:
                            st.info("Login to reply.")

            else:
                st.info("No discussions yet. Start one above! 😎")

        except Exception as e:
            st.error(f"Error loading discussions: {e}")

    # ------------------ USERS TAB ------------------
    with tab2:
        st.header("🕺 Other users in our community 💃")

        users = user_df[["username", "avatar_path"]].dropna().reset_index(drop=True)

        # Create grid of 3 per row
        for i in range(0, len(users), 3):
            row_users = users.iloc[i:i+3]
            cols = st.columns(3)

            for col, (_, row) in zip(cols, row_users.iterrows()):
                with col:
                    # Show Avatar
                    try:
                        st.image(row["avatar_path"])
                    except:
                        st.image("images/default.png")

                    # Username
                    st.markdown(
                        f"<p style='text-align:center; font-weight:bold;'>{row['username']}</p>",
                        unsafe_allow_html=True
                    )

                    st.write("")  # spacing


    # ------------------ LATEST UPDATES TAB ------------------
    with tab3:
        st.header("🔔 Latest Application Updates")
        st.info("Coming soon...")
