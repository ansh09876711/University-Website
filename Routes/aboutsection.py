from flask import Flask, app, app, render_template, request, redirect, session
# ===== ABOUT SECTION PAGES =====

@app.route("/the-university")
def the_university():
    return render_template("about/the_university.html")

@app.route("/heritage")
def heritage():
    return render_template("about/heritage.html")

@app.route("/leadership")
def leadership():
    return render_template("about/leadership.html")

@app.route("/director-message")
def director_message():
    return render_template("about/director_message.html")

@app.route("/dean-message")
def dean_message():
    return render_template("about/dean_message.html")

@app.route("/awards")
def awards():
    return render_template("about/awards.html")

@app.route("/approvals")
def approvals():
    return render_template("about/approvals.html")

@app.route("/mandatory-disclosure")
def mandatory_disclosure():
    return render_template("about/mandatory_disclosure.html")

@app.route("/vision")
def vision():
    return render_template("about/vision.html")

@app.route("/core-values")
def core_values():
    return render_template("about/core_values.html")

@app.route("/governance")
def governance():
    return render_template("about/governance.html")

@app.route("/faculties")
def faculties():
    return render_template("about/faculties.html")

@app.route("/committees")
def committees():
    return render_template("about/committees.html")

@app.route("/regulations")
def regulations():
    return render_template("about/regulations.html")

@app.route("/act")
def act():
    return render_template("about/act.html")

@app.route("/development-plan")
def development_plan():
    return render_template("about/development_plan.html")

@app.route("/collaboration")
def collaboration():
    return render_template("about/collaboration.html")