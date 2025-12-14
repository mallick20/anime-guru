import streamlit as st
from sqlalchemy import text
import time
import os
import bcrypt

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

        # Fixed avatar selection
        selected_avatar = st.radio(
            "Select Avatar",
            options=avatar_list,  # all available avatars
            index=avatar_list.index(current_avatar) if current_avatar in avatar_list else 0,
            format_func=lambda x: f"Avatar {avatar_list.index(x) + 1}",
            label_visibility="collapsed"
        )

        # Display avatars in grid with preview
        if not avatar_list:
            st.info("No avatars found.")
        else:
            columns_count = min(6, len(avatar_list))
            for i in range(0, len(avatar_list), columns_count):
                row_avatars = avatar_list[i : i + columns_count]
                cols = st.columns(len(row_avatars))
                for col, avatar in zip(cols, row_avatars):
                    with col:
                        st.image(avatar, width=100, caption=f"Avatar {avatar_list.index(avatar) + 1}")

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
            time.sleep(2)
            st.rerun()

        except Exception as e:
            st.error(f"Error updating profile: {e}")

    # ---------------- CHANGE PASSWORD ----------------
    st.divider()
    with st.expander("🔑 Change Password", expanded=False):
        with st.form("change_password_form", clear_on_submit=True):
            old_pw = st.text_input("Enter Current Password", type="password")
            new_pw = st.text_input("Enter New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            pw_submit = st.form_submit_button("Update Password", use_container_width=True)

        if pw_submit:
            if not old_pw or not new_pw or not confirm_pw:
                st.warning("Please fill all password fields.")
            elif new_pw != confirm_pw:
                st.warning("New passwords do not match.")
            else:
                try:
                    with engine.connect() as conn:
                        user_row = conn.execute(
                            text("SELECT password FROM users WHERE id = :uid"),
                            {"uid": st.session_state.user_id}
                        ).fetchone()

                    if user_row and bcrypt.checkpw(old_pw.encode('utf-8'), user_row[0].encode('utf-8')):
                        new_hashed = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        with engine.begin() as conn:
                            conn.execute(
                                text("UPDATE users SET password = :pw WHERE id = :uid"),
                                {"pw": new_hashed, "uid": st.session_state.user_id}
                            )
                        st.success("✅ Password updated successfully!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Incorrect current password.")
                except Exception as e:
                    st.error(f"Error updating password: {e}")

    # ---------------- DELETE ACCOUNT ----------------
    st.divider()
    with st.expander("⚠️ Delete Account", expanded=False):
        with st.form("delete_account_form"):
            st.warning("This action is irreversible. All your data will be permanently deleted.")
            confirm_text = st.text_input("Type DELETE to confirm")
            del_submit = st.form_submit_button("🗑️ Delete My Account", use_container_width=True)

        if del_submit:
            if confirm_text.strip().upper() == "DELETE":
                try:
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": st.session_state.user_id})

                    st.success("✅ Account deleted successfully.")
                    st.session_state.clear()
                    st.session_state.operation = "home"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting account: {e}")
            else:
                st.warning("Please type DELETE to confirm.")

    # ---------------- SCROLLABLE RECENT ACTIVITY ----------------
    st.divider()
    st.subheader("📜 Recent Activity")

    st.markdown(
        """
        <style>
        .scroll-box {
            height: 300px;
            overflow-y: scroll;
            padding: 10px;
            border: 1px solid #666;
            border-radius: 10px;
            background-color: #111;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        with engine.connect() as conn:
            logs = conn.execute(
                text("""
                    SELECT activitytype, content, activitydate 
                    FROM user_activity_history 
                    WHERE userid = :uid
                    ORDER BY activitydate DESC
                    LIMIT 25
                """),
                {"uid": st.session_state.user_id}
            ).fetchall()

        if logs:
            activity_html = ""
            for log in logs:
                activity_html += f"<p>➡️ <b>{log[0]}</b> — {log[1]}<br><span style='font-size:12px;color:#aaa;'>🕒 {log[2]}</span></p>"
            st.markdown(f"<div class='scroll-box'>{activity_html}</div>", unsafe_allow_html=True)
        else:
            st.info("No recent activity yet.")
    except Exception as e:
        st.error(f"Failed to load activity logs: {e}")