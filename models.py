from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class HeroMedia(db.Model):
    __tablename__ = "hero_media"

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255))
    type = db.Column(db.String(50))


class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    highest_package = db.Column(db.String(50))
    recruiters = db.Column(db.String(50))

    student_name = db.Column(db.String(100))
    student_image = db.Column(db.String(200))
    company_name = db.Column(db.String(100))
    company_logo = db.Column(db.String(200))

    description = db.Column(db.Text)


class PlacementStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_name = db.Column(db.String(100))
    student_image = db.Column(db.String(200))

    company_name = db.Column(db.String(100))
    company_logo = db.Column(db.String(200))

    ctc = db.Column(db.String(20))
    description = db.Column(db.Text)


class Recruiter(db.Model):
    __tablename__ = "recruiters"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100))
    company_logo = db.Column(db.String(200))
