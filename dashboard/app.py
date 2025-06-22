from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

DB_PATH = "data/membres.json"

@app.route("/")
def index():
    try:
        with open(DB_PATH, "r") as f:
            membres = json.load(f)
    except:
        membres = []

    return render_template("index.html", membres=membres)

@app.route("/refuser/<int:user_id>")
def refuser(user_id):
    with open(DB_PATH, "r") as f:
        membres = json.load(f)
    membres = [m for m in membres if m["id"] != user_id]
    with open(DB_PATH, "w") as f:
        json.dump(membres, f, indent=4)
    return redirect(url_for("index"))

@app.route("/ajouter", methods=["POST"])
def ajouter():
    username = request.form["username"]
    user_id = int(request.form["user_id"])
    with open(DB_PATH, "r") as f:
        membres = json.load(f)
    membres.append({
        "username": username,
        "id": user_id
    })
    with open(DB_PATH, "w") as f:
        json.dump(membres, f, indent=4)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
