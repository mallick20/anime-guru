import streamlit as st
import bcrypt
from datetime import date
from sqlalchemy import text
import os
import time
import re

def signup(engine, user_df, genres_list):
    st.title("📝 :blue[Sign Up for OtakuConnect]")

    # ✅ Load avatars
    import os
    avatar_folder = "images/avatars"
    avatar_files = [f"{avatar_folder}/{file}" for file in os.listdir(avatar_folder) if file.endswith(("png","jpg","jpeg"))]

    if "selected_avatar" not in st.session_state:
        st.session_state.selected_avatar = avatar_files[0] if avatar_files else None

    # ------------------ FORM START ------------------
    with st.form('sign_up'):
        FirstName = st.text_input("First Name")
        LastName = st.text_input("Last Name")
        UserName = st.text_input("User Name")
        Email = st.text_input("Enter Your Email ID")
        Dob = st.date_input(
            "Enter Your DOB",
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="MM.DD.YYYY"
        )
        Password = st.text_input("Password", type="password")
        Confirm_password = st.text_input("Confirm Password", type="password")

        # 🌸 Favorite Genres
        st.markdown("### 💖 Choose Your Top 5 Favorite Genres")
        fav_genres = st.multiselect(
            "Pick up to 5 genres:",
            genres_list,
            max_selections=5
        )

        st.markdown("Select your avatar given below before signing in!!")

        # ✅ Submit Button INSIDE form
        submit_button = st.form_submit_button("Sign Up ✅")

    # ------------------ FORM END ------------------

    # 🎭 Avatar Section (OUTSIDE form!)
    st.markdown("### 👤 Choose Your Avatar")

    cols = st.columns(5)
    for idx, avatar in enumerate(avatar_files):
        with cols[idx % 5]:
            if st.button("Select", type="primary", key=avatar):
                st.session_state.selected_avatar = avatar
            st.image(avatar)

    # Show selected avatar
    st.write("✅ Selected Avatar:")
    st.image(st.session_state.selected_avatar, width=120)

    # ------------------ PROCESS SUBMIT ------------------
    if submit_button:
        if not FirstName or not LastName or not UserName or not Email or not Password or not Confirm_password:
            st.warning("Please fill all fields.")
            return

        if Password != Confirm_password:
            st.warning("Passwords do not match.")
            return

        if UserName in user_df['username'].tolist():
            st.warning("Username already exists.")
            return

        if Email in user_df['email'].tolist():
            st.warning("Email already registered.")
            return

        if not fav_genres:
            st.warning("Pick at least 1 genre.")
            return

        # Convert genres
        fav_genres_str = ", ".join(fav_genres)

        hashed_pw = bcrypt.hashpw(Password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO users 
                        (firstname, lastname, username, email, dob, password, favoritegenres, avatar_path, accountcreateddate)
                        VALUES 
                        (:fname, :lname, :uname, :email, :dob, :pw, :genres, :avatar, NOW())
                    """),
                    {
                        "fname": FirstName,
                        "lname": LastName,
                        "uname": UserName,
                        "email": Email.lower().strip(),
                        "dob": Dob,
                        "pw": hashed_pw,
                        "genres": fav_genres_str,
                        "avatar": st.session_state.selected_avatar
                    }
                )

            st.success("✅ Account created successfully!")
            st.toast("Redirecting to login page..")
            time.sleep(2)
            st.session_state.operation = "login"
            st.rerun()

        except Exception as e:
            st.error(f"Signup failed: {e}")


def login(engine):
    st.title("🔐 :blue[Login to OtakuConnect]")

    Email = st.text_input("Email").lower().strip()
    Password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if not Email or not Password:
            st.warning("Please fill in both fields.")
            return

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM users WHERE email = :e"),
                {"e": Email}
            ).fetchone()

        if not result:
            st.error("Invalid email or password.")
            return

        # ✅ Access row properly
        try:
            stored_hash = result._mapping['password']
            user_id = result._mapping['id']
            username = result._mapping['username']
        except Exception:
            stored_hash = result['password']
            user_id = result['id']
            username = result['username']

        # ✅ Check password
        if bcrypt.checkpw(Password.encode('utf-8'), stored_hash.encode('utf-8')):

            # ✅ Update last login timestamp
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("UPDATE users SET lastlogin = NOW() WHERE id = :uid"),
                        {"uid": user_id}
                    )
            except Exception as e:
                st.warning(f"⚠️ Could not update last login: {e}")

            # ✅ Set session variables
            st.session_state.logged_in = True
            st.session_state.user_id = user_id
            st.session_state.username = username
            st.success(f"Welcome back, {username}!")
            st.session_state.operation = "home"
            st.rerun()

        else:
            st.error("Invalid email or password.")
