from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os, csv, io, statistics, re

from analytics.engine import analyze_reviews, build_recommendations

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "smart-restaurant-pbl-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///restaurant.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default="customer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    manager_name = db.Column(db.String(100), default="")
    active = db.Column(db.Boolean, default=True)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(80), default="Service")
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))
    performance_score = db.Column(db.Float, default=4.0)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    food_rating = db.Column(db.Integer, nullable=False)
    service_rating = db.Column(db.Integer, nullable=False)
    ambience_rating = db.Column(db.Integer, nullable=False)
    cleanliness_rating = db.Column(db.Integer, nullable=False)
    speed_rating = db.Column(db.Integer, nullable=False)
    overall_rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), default="Neutral")
    sentiment_score = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    order_type = db.Column(db.String(30), default="Dine-in")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission for this page.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return deco

@app.context_processor
def inject_globals():
    return {"current_user": session.get("name"), "current_role": session.get("role")}

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        u = User.query.filter_by(email=email).first()
        if u and check_password_hash(u.password_hash, password):
            session.update(user_id=u.id, name=u.name, role=u.role)
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    reviews = Review.query.all()
    restaurants = Restaurant.query.filter_by(active=True).all()
    stats = analyze_reviews(reviews)
    stats["restaurant_count"] = len(restaurants)
    stats["customer_count"] = User.query.filter_by(role="customer").count()
    stats["employee_count"] = Employee.query.count()
    stats["order_revenue"] = round(sum(o.amount for o in Order.query.all()),2)
    recs = build_recommendations(stats)
    recent = Review.query.order_by(Review.created_at.desc()).limit(8).all()
    return render_template("dashboard.html", stats=stats, recs=recs, recent=recent, restaurants=restaurants)

@app.route("/reviews", methods=["GET","POST"])
@role_required("customer","admin","manager")
def reviews():
    restaurants = Restaurant.query.filter_by(active=True).all()
    if request.method == "POST":
        try:
            vals = {k:int(request.form[k]) for k in ["food_rating","service_rating","ambience_rating","cleanliness_rating","speed_rating"]}
            comment = request.form["comment"].strip()
            if not comment:
                raise ValueError("Comment is required")
            overall = round(sum(vals.values())/5, 2)
            sentiment, score = analyze_reviews([{"comment": comment}])["single_sentiment"]
            r = Review(user_id=session["user_id"], restaurant_id=int(request.form["restaurant_id"]),
                       overall_rating=overall, comment=comment, sentiment=sentiment,
                       sentiment_score=score, **vals)
            db.session.add(r); db.session.commit()
            flash("Review submitted successfully.", "success")
            return redirect(url_for("reviews"))
        except Exception as e:
            flash("Please enter valid ratings and review text.", "danger")
    mine = Review.query.filter_by(user_id=session["user_id"]).order_by(Review.created_at.desc()).all()
    return render_template("reviews.html", restaurants=restaurants, mine=mine)

@app.route("/analytics")
@role_required("admin","manager")
def analytics():
    reviews = Review.query.all()
    stats = analyze_reviews(reviews)
    recs = build_recommendations(stats)
    return render_template("analytics.html", stats=stats, recs=recs)

@app.route("/admin")
@role_required("admin")
def admin():
    return render_template("admin.html",
        users=User.query.order_by(User.created_at.desc()).all(),
        restaurants=Restaurant.query.all(),
        employees=Employee.query.all(),
        reviews=Review.query.order_by(Review.created_at.desc()).limit(20).all())

@app.route("/admin/restaurant", methods=["POST"])
@role_required("admin")
def add_restaurant():
    db.session.add(Restaurant(name=request.form["name"], city=request.form["city"], manager_name=request.form.get("manager_name","")))
    db.session.commit()
    flash("Restaurant added.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/employee", methods=["POST"])
@role_required("admin")
def add_employee():
    db.session.add(Employee(name=request.form["name"], department=request.form.get("department","Service"),
                            restaurant_id=int(request.form["restaurant_id"]),
                            performance_score=float(request.form.get("performance_score",4))))
    db.session.commit()
    flash("Employee added.", "success")
    return redirect(url_for("admin"))

@app.route("/api/analytics")
@login_required
def api_analytics():
    return jsonify(analyze_reviews(Review.query.all()))

@app.route("/report/csv")
@role_required("admin","manager")
def report_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Restaurant","Overall","Food","Service","Ambience","Cleanliness","Speed","Sentiment","Comment","Date"])
    for r in Review.query.order_by(Review.created_at.desc()).all():
        rest = db.session.get(Restaurant, r.restaurant_id)
        writer.writerow([r.id, rest.name if rest else "", r.overall_rating, r.food_rating, r.service_rating,
                         r.ambience_rating, r.cleanliness_rating, r.speed_rating, r.sentiment, r.comment,
                         r.created_at.strftime("%Y-%m-%d")])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment; filename=restaurant_reviews.csv"})

@app.route("/report/pdf")
@role_required("admin","manager")
def report_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    stats = analyze_reviews(Review.query.all())
    c.setFont("Helvetica-Bold", 18); c.drawString(50, 800, "Smart Restaurant Analytics Report")
    c.setFont("Helvetica", 11)
    y=770
    lines = [
        f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        f"Total Reviews: {stats['total_reviews']}",
        f"Average Rating: {stats['average_rating']}/5",
        f"Customer Satisfaction: {stats['satisfaction_score']}%",
        f"Positive Reviews: {stats['sentiment']['Positive']}",
        f"Negative Reviews: {stats['sentiment']['Negative']}",
        f"Neutral Reviews: {stats['sentiment']['Neutral']}",
        "",
        "Top Service Areas:",
    ]
    for line in lines:
        c.drawString(55,y,line); y-=22
    for name,score in sorted(stats["dimensions"].items(), key=lambda x:x[1], reverse=True):
        c.drawString(70,y,f"{name.title()}: {score}/5"); y-=20
    y-=10; c.setFont("Helvetica-Bold", 12); c.drawString(55,y,"Decision Recommendations"); y-=20
    c.setFont("Helvetica", 10)
    for rec in build_recommendations(stats):
        for chunk in [rec[:105]]:
            c.drawString(70,y,"- "+chunk); y-=17
            if y < 70:
                c.showPage(); y=800; c.setFont("Helvetica",10)
    c.save(); buf.seek(0)
    return Response(buf.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition":"attachment; filename=restaurant_analytics_report.pdf"})

def seed_data():
    if User.query.first():
        return
    admin = User(name="System Admin", email="admin@smartrest.com", password_hash=generate_password_hash("admin123"), role="admin")
    manager = User(name="Restaurant Manager", email="manager@smartrest.com", password_hash=generate_password_hash("manager123"), role="manager")
    customer = User(name="Demo Customer", email="customer@smartrest.com", password_hash=generate_password_hash("customer123"), role="customer")
    db.session.add_all([admin,manager,customer]); db.session.flush()

    rests = [
        Restaurant(name="Spice Garden", city="Mumbai", manager_name="Amit Shah"),
        Restaurant(name="Urban Tadka", city="Pune", manager_name="Neha Patil"),
        Restaurant(name="Café Horizon", city="Navi Mumbai", manager_name="Rahul Mehta")
    ]
    db.session.add_all(rests); db.session.flush()

    for i, r in enumerate(rests):
        for j in range(4):
            db.session.add(Employee(name=f"Employee {i+1}{j+1}", department=["Service","Kitchen","Front Desk","Support"][j],
                                    restaurant_id=r.id, performance_score=round(random.uniform(3.4,4.8),1)))
        for j in range(8):
            db.session.add(Order(restaurant_id=r.id, amount=round(random.uniform(350,1800),2),
                                 order_type=random.choice(["Dine-in","Takeaway","Delivery"]),
                                 created_at=datetime.utcnow()-timedelta(days=random.randint(0,120))))
    comments = [
        "Amazing food and excellent staff. Very quick service.",
        "Food was good but service was slow during dinner.",
        "The ambience was beautiful and staff were friendly.",
        "Average experience. Waiting time was too long.",
        "Excellent taste, clean restaurant and helpful staff.",
        "Very disappointing service and the food was cold.",
        "Great restaurant, fast service and fresh food.",
        "Clean place but staff behaviour needs improvement.",
        "Loved the food and ambience. Will visit again.",
        "The order took too long and the experience was frustrating."
    ]
    for i in range(45):
        rest = random.choice(rests)
        cmt = random.choice(comments)
        vals = {k: max(1,min(5, int(round(random.gauss(4,0.8))))) for k in
                ["food_rating","service_rating","ambience_rating","cleanliness_rating","speed_rating"]}
        if "slow" in cmt.lower() or "long" in cmt.lower() or "disappointing" in cmt.lower():
            vals["service_rating"] = random.choice([2,3]); vals["speed_rating"] = random.choice([1,2,3])
        overall = round(sum(vals.values())/5,2)
        sentiment, score = analyze_reviews([{"comment":cmt}])["single_sentiment"]
        db.session.add(Review(user_id=customer.id, restaurant_id=rest.id, comment=cmt,
                              overall_rating=overall, sentiment=sentiment, sentiment_score=score, **vals,
                              created_at=datetime.utcnow()-timedelta(days=random.randint(0,120))))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(debug=True)
