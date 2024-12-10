from curses import flash
from flask import Flask, render_template, request, redirect, jsonify
from flask_migrate import Migrate
from models import db, Animal, Shelter, AdoptionApplication

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animal_adoption.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
def init_app(app):
    upload_folder = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route("/")
def index():
    animals = Animal.query.all()
    return render_template("index.html", animals=animals)

@app.route("/admin")
def admin():
    shelters = Shelter.query.all()
    animals = Animal.query.all()
    return render_template("admin.html", shelters=shelters, animals=animals)

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
        image = request.form["image"]
        shelter_id = int(request.form["shelter_id"])

        new_animal = Animal(
            name=name, species=species, breed=breed, age=age, 
            description=description, image=image, shelter_id=shelter_id
        )
        db.session.add(new_animal)
        db.session.commit()
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            image_url = 'default.jpg'
        elif file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            image_url = filename
        else:
            flash('Invalid file type')
            return redirect(request.url)

        return redirect("/admin")

    shelters = Shelter.query.all()
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

@app.route("/api/animals", methods=["GET"])
def get_animals():
    animals = Animal.query.all()
    animal_list = [{"name": a.name, "species": a.species, "breed": a.breed, "age": a.age, 
                    "description": a.description, "image": a.image} for a in animals]
    return jsonify(animal_list)

@app.route("/api/shelters", methods=["GET"])
def get_shelters():
    shelters = Shelter.query.all()
    shelters_list = [{"name": s.name, "address": s.address} for s in shelters]
    return jsonify(shelters_list)

if __name__ == "__main__":
    app.run(debug=True)
