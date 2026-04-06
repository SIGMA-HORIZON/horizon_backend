
from horizon.infrastructure.database import engine
from sqlalchemy import text

def drop_everything():
    with engine.connect() as conn:
        print("Dropping all tables...")
        # Get all tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS \"{table}\" CASCADE"))
            print(f"Dropped table: {table}")
        
        print("Dropping all enums...")
        # Get all enums
        result = conn.execute(text("SELECT typname FROM pg_type WHERE typcategory = 'E'"))
        enums = [row[0] for row in result.fetchall()]
        for enum in enums:
            conn.execute(text(f"DROP TYPE IF EXISTS \"{enum}\" CASCADE"))
            print(f"Dropped enum: {enum}")
            
        conn.commit()
    print("Database is clean.")

if __name__ == "__main__":
    drop_everything()
