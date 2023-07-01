from flask import Flask, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import requests
import datetime
import json
import re
from otherfuncs import convertTime

app = Flask(__name__)

db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'EFW(*ENR(WE*NIVn9esi27ESFPOf^erwsaiWNMF*)'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)

db.init_app(app)

api_key = "AIzaSyBYWjdRWpzw97F1VLqH116Vry8i_jqlzbk"

class User(UserMixin, db.Model): 

    def get_id(self):
           return (self.email)
    
    fname = db.Column(db.String(50))
    lname = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, primary_key=True)
    phone = db.Column(db.String(50), unique=True)
    zipcode = db.Column(db.String(5))
    password = db.Column(db.String(64))

class Cleanups(db.Model): 

    def get_id(self):
           return (self.id)
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(500))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    date = db.Column(db.String(20))
    lat = db.Column(db.String(100))
    lng = db.Column(db.String(100))
    description = db.Column(db.String(2000))
    type = db.Column(db.String(25))
    amountofsignups = db.Column(db.Integer)

class User_Cleanups(db.Model): 

    def get_id(self):
           return (self.id)
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100))
    cleanup_id = db.Column(db.Integer)
    
db.create_all()

@login_manager.user_loader
def load_user(email):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(email)

@app.route("/", methods = ["POST", "GET"])
def homePage():
    if request.method == "GET":
        return render_template("index.html", user = current_user)
    
    elif request.method == "POST":
        pass

@app.route("/logout", methods = ["POST", "GET"])
@login_required
def logout():
    if request.method == "GET":
        logout_user()
        flash("Logged out successfully!")
        return redirect("/login")

@app.route("/dashboard", methods = ["POST", "GET"])
@login_required
def dashboard():
    if request.method == "GET":
        zipcode = current_user.zipcode
        zip_info = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={zipcode}&key={api_key}").json()
        allcleanups = [{"id": cleanup.id, "address": cleanup.address, "start_time": convertTime(cleanup.start_time), "end_time": convertTime(cleanup.end_time), "date": cleanup.date, "lat": cleanup.lat, "lng": cleanup.lng, "description": cleanup.description, "type": cleanup.type, "amountofsignups" : cleanup.amountofsignups} for cleanup in Cleanups.query.all()]

        curusercleanupspre = User_Cleanups.query.filter_by(user_email=current_user.email).all()
        curusercleanupspre = [usercleanup.cleanup_id for usercleanup in curusercleanupspre]
        curusercleanups = []

        for curusercleanup in curusercleanupspre:
            print(curusercleanup)
            actualcurusercleanup = Cleanups.query.filter_by(id=curusercleanup).first()
            curusercleanups.append({"id": actualcurusercleanup.id, "address": actualcurusercleanup.address, "start_time": convertTime(actualcurusercleanup.start_time), "end_time": convertTime(actualcurusercleanup.end_time), "date": actualcurusercleanup.date, "lat": actualcurusercleanup.lat, "lng": actualcurusercleanup.lng, "description": actualcurusercleanup.description, "type": actualcurusercleanup.type, "amountofsignups": actualcurusercleanup.amountofsignups})

        print(curusercleanups)

        nonusercleanups = [cleanup for cleanup in allcleanups if cleanup["id"] not in curusercleanupspre]

        return render_template("dashboard.html", cleanups = json.dumps(nonusercleanups), curusercleanups = curusercleanups, user = current_user, location = zip_info.get("results")[0].get("geometry").get("location"), api_key = api_key, curdate = str(datetime.date.today() + datetime.timedelta(days=1)))
    
    elif request.method == "POST":

        print(request.form)

        if any(re.match(r'^leavecleanup\d+$', key) for key in request.form):

            formname = ""
            for key in request.form:
                formname = key

            cleanupid = formname.replace("leavecleanup", "")

            print(cleanupid)

            usercleanup = User_Cleanups.query.filter_by(user_email=current_user.email, cleanup_id=cleanupid).first()

            db.session.delete(usercleanup)
            db.session.commit()

            Cleanups.query.filter_by(id=cleanupid).first().amountofsignups -= 1

            db.session.commit()

            if Cleanups.query.filter_by(id=cleanupid).first().amountofsignups == 0:
                db.session.delete(Cleanups.query.filter_by(id=cleanupid).first())
                alldeletequeries = User_Cleanups.query.filter_by(cleanup_id=cleanupid).all()
                for query in alldeletequeries:
                    db.session.delete(query)
                    db.session.commit()
                db.session.commit()

            

            return redirect("/dashboard")

        elif any(re.match(r'^joincleanup\d+$', key) for key in request.form):
            formname = ""

            for key in request.form:
                formname = key

            cleanupid = formname.replace("joincleanup", "")

            usercleanup = User_Cleanups(user_email=current_user.email, cleanup_id=cleanupid)

            db.session.add(usercleanup)

            db.session.commit()

            Cleanups.query.filter_by(id=cleanupid).first().amountofsignups += 1

            db.session.commit()

            return redirect("/dashboard")
        

        address = request.form.get("address2")
        start_time = request.form.get("starttime")
        end_time = request.form.get("endtime")
        date = request.form.get("date")
        description = request.form.get("description")
        typeOfCleanup = request.form.get("typeOfCleanup")
        othertypeoftrail = request.form.get("othertypeoftrail")

        if start_time > end_time:
            flash("Start time cannot be after end time!")
            return redirect("/dashboard")
        
        if typeOfCleanup == "other":
            typeOfCleanup = othertypeoftrail
        
        addressInfo = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}").json()
        lat = addressInfo.get("results")[0].get("geometry").get("location").get("lat")
        lng = addressInfo.get("results")[0].get("geometry").get("location").get("lng")

        new_cleanup = Cleanups(address=address, start_time=start_time, end_time=end_time, date=date, lat=lat, lng=lng, description=description, type=typeOfCleanup, amountofsignups=1)
        db.session.add(new_cleanup)
        db.session.commit()


        usercleanup = User_Cleanups(user_email=current_user.email, cleanup_id=new_cleanup.id)
        db.session.add(usercleanup)
        db.session.commit()

        return redirect("/dashboard")

@app.route("/login", methods = ["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect("/dashboard")
    if request.method == "GET":
        return render_template("login.html", user = current_user)
    
    elif request.method == "POST":
        
        email = request.form.get("email")
        password = request.form.get("password")
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Please check your login details and try again.")
            return redirect("/login")
            
        
        login_user(user)

        return redirect("/dashboard")

@app.route("/signup", methods = ["POST", "GET"])
def signup():
    if current_user.is_authenticated:    
        return redirect("/dashboard")
    if request.method == "GET":
        return render_template("signup.html", user = current_user)
    
    elif request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        phone = request.form.get("phone")
        zipcode = request.form.get("zipcode")
        password = request.form.get("password")
        confirm_password = request.form.get("password2")

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect("/signup")
        
        elif User.query.filter_by(email=email).first():
            flash("Email already exists!")
            return redirect("/signup")
        
        hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(fname=fname, lname=lname, email=email, phone=phone, zipcode=zipcode, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True, port = 3000, host='0.0.0.0')