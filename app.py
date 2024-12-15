from flask import Flask, render_template, request, redirect, jsonify, flash, send_from_directory
from flask_migrate import Migrate
from models import db, Animal, Shelter, AdoptionApplication
from werkzeug.utils import secure_filename
import os
import uuid
import ssl
from authlib.integrations.flask_client import OAuth
from flask import session, url_for, redirect
from dotenv import load_dotenv
from flask_mail import Mail, Message 

app = Flask(__name__)

load_dotenv()

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animal_adoption.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

upload_folder = os.path.join(app.root_path, 'uploads')
os.makedirs(upload_folder, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_folder

db.init_app(app)
migrate = Migrate(app, db)

load_dotenv()

oauth = OAuth(app)
google_oauth = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.route("/login")
def login():
    session['nonce'] = str(uuid.uuid4())  # Generate and store a nonce
    redirect_uri = url_for("authorized", _external=True)
    return google_oauth.authorize_redirect(redirect_uri)


@app.route("/authorized")
def authorized():
    token = google_oauth.authorize_access_token()
    try:
        # Automatically parse the ID token without manually handling nonce
        user_info = token.get("userinfo")
        session["google_user"] = user_info
        return redirect("/admin")
    except Exception as e:
        return f"Authorization failed: {str(e)}"


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
    if "google_user" not in session:
        return redirect(url_for("login"))

    shelters = Shelter.query.all()
    animals = Animal.query.all()
    adoption_applications = AdoptionApplication.query.order_by(AdoptionApplication.status).all()
    if not shelters:
        shelters = []  
    if not animals:
        animals = []  
    return render_template("admin.html", shelters=shelters, animals=animals, adoption_applications=adoption_applications)

@app.route("/admin/delete-shelter/<int:id>", methods=["POST"])
def delete_shelter(id):
    shelter = Shelter.query.get_or_404(id)
    animals = Animal.query.filter_by(shelter_id=id).all()
    for animal in animals:
        delete_animal(animal.id)
    db.session.delete(shelter)
    db.session.commit()
    flash("Shelter deleted successfully!")
    return redirect("/admin")

@app.route("/admin/delete-animal/<int:id>", methods=["POST"])
def delete_animal(id):
    animal = Animal.query.get_or_404(id)
    adoption_applications = AdoptionApplication.query.filter_by(animal_id=id).all()
    for adoption in adoption_applications:
        if adoption.status == 'Pending':
            reject_application(adoption.id)
        db.session.delete(adoption)
        db.session.commit()
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

@app.route('/admin/application/<int:id>/approve', methods=['POST'])
def approve_application(id):
    print(f"Processing approval for Application ID: {id}")  # Debugging
    application = AdoptionApplication.query.get_or_404(id)
    print(f"Application ID: {application.id}, Current Status: {application.status}")

    if application.status != 'Pending':
        flash(f"Application {id} cannot be modified.", 'danger')
        return redirect('/admin')

    try:
        application.status = 'Approved'
        db.session.commit()
        print(f"Application ID: {id} status updated to 'Approved'.")
        
        send_email(
            recipient=application.email,
            subject='Adoption Application Approved',
            body=f"""
                Dear {application.name},

                Congratulations! Your adoption application for {application.animal.name} has been approved.

                Best regards,
                The Adoption Team
            """
        )
        print(f"Email sent to {application.email}")
        flash(f"Application {id} approved and email sent to {application.email}.", 'success')

        animal_id = application.animal_id
        adoption_applications = AdoptionApplication.query.filter_by(animal_id=animal_id).all()
        for adoption in adoption_applications:
            if adoption.status == 'Pending':
                reject_application(adoption.id)

    except Exception as e:
        print(f"Error during approval process for Application ID: {id}: {e}")
        flash(f"An error occurred while approving Application {id}.", 'danger')
    
    return redirect('/admin')

@app.route('/admin/application/<int:id>/reject', methods=['POST'])
def reject_application(id):
    application = AdoptionApplication.query.get_or_404(id)
    print(f"Processing rejection for Application ID: {application.id}, Current Status: {application.status}")  # Debugging

    if application.status == 'Rejected':
        flash(f'Application {id} is already rejected.', 'info')
        return redirect('/admin')

    if application.status == 'Approved':
        flash(f'Application {id} has already been approved and cannot be rejected.', 'warning')
        return redirect('/admin')

    if application.status == 'Pending':
        try:
            # Update application status
            application.status = 'Rejected'
            db.session.commit()

            # Send rejection email
            send_email(
                recipient=application.email,
                subject='Adoption Application Rejected',
                body=f"""
                    Dear {application.name},

                    We regret to inform you that your adoption application for {application.animal.name} has been rejected.

                    Best regards,
                    Purrfect Match
                """
            )
            flash(f'Application {id} rejected and email sent to {application.email}.', 'danger')
        except Exception as e:
            flash(f'Error while rejecting Application {id}: {str(e)}', 'danger')
    else:
        flash(f'Application {id} cannot be modified.', 'danger')

    return redirect('/admin')


# Helper Function to Send Emails
def send_email(recipient, subject, body):
    try:
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        mail.send(msg)
        print(f"Email sent to {recipient}. Subject: {subject}")  # Debugging
        return True
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")  # Debugging
        return False


@app.route('/test-email')
def test_email():
    success = send_email(
        recipient='your_email@example.com',
        subject='Test Email',
        body='This is a test email sent from the Flask app.'
    )
    if success:
        return 'Email sent successfully!'
    else:
        return 'Email failed to send.'
    
@app.route('/debug/update-status/<int:id>/<string:status>', methods=['GET'])
def debug_update_status(id, status):
    application = AdoptionApplication.query.get_or_404(id)
    try:
        application.status = status
        db.session.commit()
        return f"Application {id} status updated to {status}."
    except Exception as e:
        return f"Error: {e}"

@app.route('/debug/application/<int:id>', methods=['GET'])
def debug_application(id):
    application = AdoptionApplication.query.get_or_404(id)
    return f"Application ID: {application.id}, Status: {application.status}"


@app.route("/animals")
def browse_animals():
    animals = Animal.query.all()

    current_animal_index = int(request.args.get('index', 0))

    animal = animals[current_animal_index] if current_animal_index < len(animals) else None

    return render_template("browse_animal.html", animal=animal, current_animal_index=current_animal_index, total_animals=len(animals))

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

@app.route('/apply/<int:animal_id>', methods=['GET', 'POST'])
def apply_for_adoption(animal_id):
    animal = Animal.query.get_or_404(animal_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        print(f"Received Data: Name={name}, Email={email}, Phone={phone}, Message={message}")

        new_application = AdoptionApplication(
            animal_id=animal.id,
            name=name,
            email=email,
            phone=phone,
            message=message,
            status='Pending'
        )

        try:
            db.session.add(new_application)
            db.session.commit()
            flash('Your adoption application has been submitted successfully!', 'success')
            print("Flash message: Application submitted successfully!")  #Debugging line
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your application. Please try again.', 'danger')
            print(f"Flash message: Error - {str(e)}")  #Debug  line/delete later

    return render_template('adoption_application.html', animal=animal)


@app.route('/api/animals', methods=['GET'])
def get_animals():
    animals = Animal.query.all()
    animal_list = [
        {
            "id": animal.id,
            "name": animal.name,
            "species": animal.species,
            "breed": animal.breed,
            "age": animal.age,
            "description": animal.description,
            "image": animal.image,
        }
        for animal in animals
    ]
    return jsonify(animal_list)

if __name__ == "__main__":
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain("cert/apache-selfsigned.crt", "cert/apache-selfsigned.key")
    app.run(host="0.0.0.0", port=443, ssl_context=ssl_context, debug=True)