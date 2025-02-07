
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Notes model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Create the database
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    notes = Note.query.filter_by(user_id=user_id).all()
    return render_template("index.html", notes=notes)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "Username already exists!"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        return redirect("/")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            return redirect("/")
        return "Invalid credentials!"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")

@app.route("/add_note", methods=["POST"])
def add_note():
    if "user_id" not in session:
        return "Unauthorized", 403

    content = request.form["note"]
    if content:
        new_note = Note(user_id=session["user_id"], content=content)
        db.session.add(new_note)
        db.session.commit()
        return f'<li id="note-{new_note.id}">{new_note.content} <button hx-get="/delete_note/{new_note.id}" hx-target="#note-{new_note.id}" hx-swap="outerHTML">🗑️</button></li>'
    
    return "", 204

@app.route("/delete_note/<int:note_id>", methods=["GET"])
def delete_note(note_id):
    if "user_id" not in session:
        return "Unauthorized", 403

    note = Note.query.get(note_id)
    if note and note.user_id == session["user_id"]:
        db.session.delete(note)
        db.session.commit()
    
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))