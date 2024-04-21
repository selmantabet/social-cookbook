
# Initilaize the Flask app
from app import app, db
import models

# Initialize models
with app.app_context():
    input("Press Enter to create the database..")
    db.create_all()
    db.session.commit()
print("Database created.")
