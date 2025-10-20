from sqlalchemy import text
from datetime import datetime

def log_user_activity(engine, userid, entityid, entitytype_id, activitytype_id, content):
    """
    Log a user's activity into user_activity_history table.
    """
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO user_activity_history 
                    (userid, entityid, entitytype, activitytype, content, activitydate)
                    VALUES (:userid, :entityid, :entitytype, :activitytype, :content, :activitydate)
                """),
                {
                    "userid": userid,
                    "entityid": entityid,
                    "entitytype": entitytype_id,
                    "activitytype": activitytype_id,
                    "content": content,
                    "activitydate": datetime.now()
                }
            )
    except Exception as e:
        print(f"⚠️ Error logging activity: {e}")
