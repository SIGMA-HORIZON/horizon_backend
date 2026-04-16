
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Update admin.tamegue with the full correct email and ensure SUPER_ADMIN role
    print("Promoting/Updating admin.tamegue to tameguedonald@gmail.com...")
    result = conn.execute(
        text("""
            UPDATE users 
            SET email = 'tameguedonald@gmail.com', 
                role = 'SUPER_ADMIN', 
                is_active = true 
            WHERE username = 'admin.tamegue'
        """)
    )
    conn.commit()
    if result.rowcount == 0:
        # If the user doesn't exist for some reason, we should know
        print("User admin.tamegue not found. Checking for any user with that email...")
        result = conn.execute(text("SELECT username FROM users WHERE email = 'tameguedonald@gmail.com'"))
        row = result.fetchone()
        if row:
            print(f"Found user {row[0]} with that email, updating their role...")
            conn.execute(text("UPDATE users SET role = 'SUPER_ADMIN' WHERE email = 'tameguedonald@gmail.com'"))
            conn.commit()
        else:
            print("No user found with either username or email.")
    else:
        print("Successfully updated admin.tamegue.")
