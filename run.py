from app import app
import os
from config import Config

if __name__ == '__main__':
    # Double check database path on start
    if not os.path.exists(Config.DATABASE_PATH):
        from init_db import initialize_database, seed_data
        initialize_database()
        seed_data()
        
    app.run(debug=True, port=5000)
