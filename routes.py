from flask import Blueprint, render_template

registrar = Blueprint("registrar", __name__)

# ================= Academic Records Page =================

@registrar.route("/registrar/academic-records")
def academic_records():
    return render_template("academic_records.html")