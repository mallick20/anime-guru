import streamlit as st
import bcrypt
from datetime import date
from sqlalchemy import text
import time
import re

def signup(engine, user_df, genres_list):
    st.title("📝 :blue[Sign Up for OtakuConnect]")

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

        # 🌸 New: Favorite Genre Selector
        st.markdown("### 💖 Choose Your Top 5 Favorite Genres")
        fav_genres = st.multiselect(
            "Pick up to 5 genres you love most:",
            genres_list,
            max_selections=5
        )

        submit_button = st.form_submit_button("Sign Up", type='primary')

    if submit_button:
        # ✅ Validation Checks
        if not FirstName or not LastName or not UserName or not Email or not Dob or not Password or not Confirm_password:
            st.warning('Please fill all the fields before submitting.')
            return

        if UserName in list(user_df['username']):
            st.warning("Username already exists, please choose another!")
            return

        if Email in list(user_df['email']):
            st.warning("Email already registered, please log in instead.")
            return

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', Email):
            st.warning("Please enter a valid email address.")
            return

        if Password != Confirm_password:
            st.warning('Passwords do not match.')
            return

        if not fav_genres or len(fav_genres) == 0:
            st.warning("Please select at least one favorite genre.")
            return

        if len(fav_genres) > 5:
            st.warning("You can only select up to 5 genres.")
            return

        # ✅ Convert list to a single string
        fav_genres_str = ", ".join(fav_genres)

        # ✅ Hash password
        hashed_pw = bcrypt.hashpw(Password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # ✅ Insert safely
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO users 
                            (firstname, lastname, username, email, dob, password, favoritegenres, accountcreateddate)
                        VALUES 
                            (:fname, :lname, :uname, :email, :dob, :pw, :favgenres, NOW())
                    """),
                    {
                        "fname": FirstName.strip(),
                        "lname": LastName.strip(),
                        "uname": UserName.strip(),
                        "email": Email.lower().strip(),
                        "dob": Dob,
                        "pw": hashed_pw,
                        "favgenres": fav_genres_str
                    }
                )

            st.success("✅ Account created successfully! Redirecting you to login page...")
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
