from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Shelter(db.Model):
    __tablename__ = 'Shelter'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    
    animals = db.relationship('Animal', back_populates='shelter')


class Animal(db.Model):
    __tablename__ = 'Animal'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255), nullable=False)
    likes = db.Column(db.Integer, default=0)
    matched = db.Column(db.Boolean, default=False)  
    shelter_id = db.Column(db.Integer, db.ForeignKey('Shelter.id'), nullable=False)

    shelter = db.relationship('Shelter', back_populates='animals')


class AdoptionApplication(db.Model):
    __tablename__ = 'AdoptionApplication'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    animal_id = db.Column(db.Integer, db.ForeignKey('Animal.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    message = db.Column(db.Text)

    animal = db.relationship('Animal', backref='applications')
