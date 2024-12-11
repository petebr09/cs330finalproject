from app import app, db
from models import Shelter

# Use Flask's application context
with app.app_context():
    # Add test data
    new_shelter = Shelter(name="Test Shelter", address="123 Test Street")
    db.session.add(new_shelter)
    db.session.commit()

    print("Shelter added successfully!")
