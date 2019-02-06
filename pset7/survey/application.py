#Submit the form and read it in the datasheet
import cs50
import csv

from flask import Flask, jsonify, redirect, render_template, request

# Configure application
app = Flask(__name__)

# Reload templates when they are changed
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
def get_index():
    return redirect("/form")


@app.route("/form", methods=["GET"])
def get_form():
    return render_template("form.html")


@app.route("/form", methods=["POST"])
def post_form():
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    gender = request.form.get("gender")
    nation = request.form.get("nation")
    if not firstname or not lastname or not gender or not nation:
        return render_template("error.html", message="Form Not complete")
    with open("survey.csv", "a") as file:
        writer = csv.DictWriter(file, fieldnames=["firstname", "lastname", "gender", "nation"])
        writer.writerow({"firstname": firstname, "lastname": lastname, "gender": gender, "nation": nation })
    return redirect("/sheet")


@app.route("/sheet")
def get_sheet():
    with open("survey.csv", "r") as file:
        reader = csv.DictReader(file)
        students = list(reader)
    return render_template("survey.html", students=students)

