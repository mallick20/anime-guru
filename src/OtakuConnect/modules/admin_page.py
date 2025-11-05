import streamlit as st
import pandas as pd
from sqlalchemy import text

def admin_panel(engine):
    st.title("⚙️ Admin Dashboard")

    # --- Define admin tiles ---
    options = ["Update Role", "Revoke/Restore User", "Feedback Approval"]
    if st.session_state.role_id == '3':
        options.append("View Logs")  # Superuser only

    # --- Session state to remember selected page ---
    if "selected_admin_page" not in st.session_state:
        st.session_state.selected_admin_page = "Update Role"  # default page

    # --- Display tiles as styled buttons ---
    st.subheader("Select Admin Activity")
    cols = st.columns(len(options))
    for i, option in enumerate(options):
        # Red tile styling
        if cols[i].button(option, key=f"tile_{option}", help=f"Go to {option}"):
            st.session_state.selected_admin_page = option

    page = st.session_state.selected_admin_page

    # --- Load data once ---
    users_df = pd.read_sql(
        "SELECT id, firstname, lastname, username, email, roleid, accountstatus FROM users", 
        engine
    )

    # -------------------
    if page == "Update Role":
        st.subheader("👤 Update User Role")
        selected_user = st.selectbox("Select a user:", users_df["username"].tolist())
        if selected_user:
            user_row = users_df[users_df["username"] == selected_user].iloc[0]
            st.write(f"**Current Role:** {user_row.roleid}")

            new_role = st.selectbox("Change Role:", ["User", "Admin", "Superuser"], index=int(user_row.roleid) - 1)
            if st.button("Update Role", key="update_role_btn"):
                roleid = {"User": '1', "Admin": '2', "Superuser": '3'}[new_role]
                with engine.begin() as conn:
                    conn.execute(text("UPDATE users SET roleid = :r WHERE username = :u"), {"r": roleid, "u": selected_user})
                st.success(f"✅ Role updated to {new_role} for {selected_user}")
                st.rerun()

    # -------------------
    elif page == "Revoke/Restore User":
        st.subheader("🚫 Revoke or Restore User Access")
        selected_user = st.selectbox("Select a user:", users_df["username"].tolist())
        if selected_user:
            user_row = users_df[users_df["username"] == selected_user].iloc[0]
            st.write(f"**Account Status:** {user_row.accountstatus}")

            if user_row.accountstatus == 'Active' and st.button("Revoke Access 🚫", key="revoke_btn"):
                with engine.begin() as conn:
                    conn.execute(text("UPDATE users SET accountstatus = 'Inactive' WHERE username = :u"), {"u": selected_user})
                st.warning(f"User {selected_user}'s access revoked.")
                st.rerun()

            elif user_row.accountstatus == 'Inactive' and st.button("Restore Access ✅", key="restore_btn"):
                with engine.begin() as conn:
                    conn.execute(text("UPDATE users SET accountstatus = 'Active' WHERE username = :u"), {"u": selected_user})
                st.success(f"User {selected_user} reactivated.")
                st.rerun()

    # -------------------
    elif page == "Feedback Approval":
        st.subheader("📝 Approve Feedback")
        feedback_df = pd.read_sql(
            "SELECT * FROM feedback_table WHERE moderatedstatus = 'Pending'", 
            engine
        )
        if feedback_df.empty:
            st.info("No pending feedback to approve.")
        else:
            st.dataframe(feedback_df)
            feedback_id = st.selectbox("Select feedback to approve:", feedback_df["id"].tolist())
            if st.button("Approve Feedback", key="approve_feedback_btn"):
                with engine.begin() as conn:
                    conn.execute(text(
                        "UPDATE feedback_table SET moderatedstatus = 'Approved' WHERE id = :fid"
                    ), {"fid": feedback_id})
                st.success("Feedback approved successfully.")
                st.rerun()

    # -------------------
    elif page == "View Logs" and st.session_state.role_id == '3':
        st.subheader("🧙‍♂️ Superuser Controls: View Logs")
        logs_df = pd.read_sql(
            "SELECT * FROM user_activity_history ORDER BY activitydate DESC LIMIT 50", 
            engine
        )
        st.dataframe(logs_df)
