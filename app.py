from flask import Flask, render_template, request, redirect, jsonify, flash, send_from_directory
from flask_migrate import Migrate
from models import db, Animal, Shelter, Match, AdoptionApplication
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animal_adoption.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

upload_folder = os.path.join(app.root_path, 'uploads')
os.makedirs(upload_folder, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_folder

db.init_app(app)
migrate = Migrate(app, db)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def index():
    animals = Animal.query.all()
    return render_template("index.html", animals=animals)

@app.route("/admin")
def admin():
    shelters = Shelter.query.all()
    animals = Animal.query.all()
    if not shelters:
        shelters = []  
    if not animals:
        animals = []  
    return render_template("admin.html", shelters=shelters, animals=animals)

@app.route("/admin/delete-shelter/<int:id>", methods=["POST"])
def delete_shelter(id):
    shelter = Shelter.query.get_or_404(id)
    db.session.delete(shelter)
    db.session.commit()
    flash("Shelter deleted successfully!")
    return redirect("/admin")

@app.route("/admin/delete-animal/<int:id>", methods=["POST"])
def delete_animal(id):
    animal = Animal.query.get_or_404(id)
    db.session.delete(animal)
    db.session.commit()
    flash("Animal deleted successfully!")
    return redirect("/admin")

@app.route("/animals/<int:id>")
def animal_detail(id):
    animal = Animal.query.get_or_404(id)
    return render_template("animal_detail.html", animal=animal)

@app.route("/admin/add-animal", methods=["GET", "POST"])
def add_animal():
    if request.method == "POST":
        name = request.form["name"]
        species = request.form["species"]
        breed = request.form["breed"]
        age = int(request.form["age"])
        description = request.form["description"]
        shelter_id = int(request.form["shelter_id"])

        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = filename
        else:
            image_url = 'default.jpg'

        new_animal = Animal(
            name=name, species=species, breed=breed, age=age,
            description=description, image=image_url, shelter_id=shelter_id
        )
        db.session.add(new_animal)
        db.session.commit()
        return redirect("/admin")

    shelters = Shelter.query.all()
    if not shelters:
        shelters = [] 
    return render_template("add_animal.html", shelters=shelters)

@app.route("/admin/add-shelter", methods=["GET", "POST"])
def add_shelter():
    if request.method == "POST":
        name = request.form["name"]
        address = request.form["address"]

        new_shelter = Shelter(name=name, address=address)
        db.session.add(new_shelter)
        db.session.commit()
        return redirect("/admin")

    return render_template("add_shelter.html")

@app.route("/match")
def match_page():
    matches = Match.query.filter_by(matched=True).all()
    return render_template("matches.html", matches=matches)

@app.route("/animals")
def browse_animals():
    animals = Animal.query.all()
    animals_data = [
        {
            "id": animal.id,
            "name": animal.name,
            "description": animal.description,
            "image": animal.image,
        }
        for animal in animals
    ]
    return render_template("browse_animal.html", animals=animals_data)

@app.route("/search")
def search_animals():
    name = request.args.get("name", "").strip()
    animal_type = request.args.get("type", "").strip()
    shelter_id = request.args.get("shelter", "").strip()

    query = Animal.query

    if name:
        query = query.filter(Animal.name.ilike(f"%{name}%"))
    if animal_type:
        query = query.filter(Animal.species.ilike(f"%{animal_type}%"))
    if shelter_id:
        query = query.filter(Animal.shelter_id == shelter_id)

    animals = query.all()
    shelters = Shelter.query.all()
    species = db.session.query(Animal.species).distinct().all()

    species_list = [s[0] for s in species]
    return render_template("search_animal.html", animals=animals, shelters=shelters, species_list=species_list)

@app.route("/admin/edit-animal/<int:id>", methods=["GET", "POST"])
def edit_animal(id):
    animal = Animal.query.get_or_404(id)
    shelters = Shelter.query.all()

    if request.method == "POST":
        animal.name = request.form["name"]
        animal.species = request.form["species"]
        animal.breed = request.form["breed"]
        animal.age = int(request.form["age"])
        animal.description = request.form["description"]
        animal.shelter_id = int(request.form["shelter_id"])

        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            animal.image = filename

        db.session.commit()
        flash("Animal updated successfully!")
        return redirect("/admin")

    return render_template("edit_animal.html", animal=animal, shelters=shelters)

@app.route("/admin/edit-shelter/<int:id>", methods=["GET", "POST"])
def edit_shelter(id):
    shelter = Shelter.query.get_or_404(id)

    if request.method == "POST":
        shelter.name = request.form["name"]
        shelter.address = request.form["address"]

        db.session.commit()
        flash("Shelter updated successfully!")
        return redirect("/admin")

    return render_template("edit_shelter.html", shelter=shelter)

if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
        app.run(debug=True)
