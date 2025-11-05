import streamlit as st
from sqlalchemy import text
from datetime import date
import os

def profile(user_df, engine):
    st.title("👤 Your Profile")

    image_values = {
        'images/avatars/boy_avatar1.png': 1,
        'images/avatars/boy_avatar2.png': 2,
        'images/avatars/boy_avatar3.png': 3,
        'images/avatars/girl_avatar1.png': 4,
        'images/avatars/girl_avatar2.png': 5,
        'images/avatars/girl_avatar3.png': 6
    }

    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        return

    # Load user info
    user_info = user_df[user_df["username"] == st.session_state.username].iloc[0]
    current_avatar = user_info.get("avatar_path", "images/default.png")

    # Avatar list
    avatar_folder = "images/avatars"
    avatar_list = [
        f"{avatar_folder}/{file}"
        for file in os.listdir(avatar_folder)
        if file.endswith(("png", "jpg", "jpeg"))
    ]

    # Avatar preview
    st.image(user_info["avatar_path"], width=250)

    st.write(f"**:violet[Username]:** {user_info['username']}")
    st.write(f"**:violet[Name]:** {user_info['firstname']} {user_info['lastname']}")
    st.write(f"**:violet[Email]:** {user_info['email']}")
    st.write(f"**:violet[Favorite Genres]:** {user_info['favoritegenres']}")
    st.write(f"**:violet[Account Created]:** {user_info['accountcreateddate']}")

    st.divider()
    st.subheader("✏️ Edit Profile")

    with st.form("edit_profile_form"):
        new_email = st.text_input("Update Email", value=user_info['email'])
        new_genres = st.text_input("Update Favorite Genres", value=user_info["favoritegenres"])

        st.write("### Change Avatar")

        # 🧩 Fixed avatar selection
        selected_avatar = st.radio(
            "Select Avatar",
            avatar_list,  # all available avatars
            index=avatar_list.index(current_avatar) if current_avatar in avatar_list else 0,
            format_func=lambda x: f"Avatar {image_values.get(x, '?')}",
            label_visibility="collapsed"
        )

        # 🖼️ Display avatars in grid with preview
        cols = st.columns(6)
        for idx, avatar in enumerate(avatar_list):
            with cols[idx % 6]:
                st.image(avatar, width=100, caption=f"Avatar {image_values.get(avatar, '?')}")

        submit_edit = st.form_submit_button("💾 Update Profile", use_container_width=True)

    if submit_edit:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE users 
                        SET email = :email, favoritegenres = :genres, avatar_path = :avatar
                        WHERE id = :uid
                    """),
                    {
                        "email": new_email.strip(),
                        "genres": new_genres.strip(),
                        "avatar": selected_avatar,
                        "uid": st.session_state.user_id
                    }
                )
            st.success("✅ Profile updated successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Error updating profile: {e}")

    st.divider()
    st.subheader("📜 Recent Activity")

    try:
        with engine.connect() as conn:
            logs = conn.execute(
                text("""
                    SELECT activitytype, content, activitydate 
                    FROM user_activity_history 
                    WHERE userid = :uid
                    ORDER BY activitydate DESC
                    LIMIT 10
                """),
                {"uid": st.session_state.user_id}
            ).fetchall()

        if logs:
            for log in logs:
                st.write(f"➡️ **{log[0]}** — {log[1]}")
                st.caption(f"🕒 {log[2]}")
        else:
            st.info("No activity yet.")
    except Exception as e:
        st.error(f"Failed to load activity logs: {e}")
