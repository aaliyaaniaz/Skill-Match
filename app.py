from flask import Flask, render_template, request, redirect, session, url_for, flash 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillmatch.db'
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # plain password (simple version)
    skill_teach = db.Column(db.String(100), nullable=False)
    skill_learn = db.Column(db.String(100), nullable=False)

# Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Home route
@app.route('/')
def home():
    return render_template("index.html")

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("Request method:", request.method)
    if request.method == 'POST':
        print(request.form)
        username = request.form['username']
        password = request.form['password']
        skill_teach = request.form['skill_teach']
        skill_learn = request.form['skill_learn']

        # ✅ Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("" \
            "User already exists! Please log in.", "warning")
            return redirect(url_for('login'))

        # ✅ Save new user
        new_user = User(
            username=username,
            password=password,
            skill_teach=skill_teach,
            skill_learn=skill_learn
        )
        db.session.add(new_user)
        db.session.commit()

        flash(" Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("signup.html")

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash(" Invalid username or password!", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")

# Dashboard (matches)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash(" Please log in first!", "warning")
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])

    # Find matches (case-insensitive)
    matches = User.query.filter(
       func.lower(User.skill_teach) == func.lower(current_user.skill_learn),
       func.lower(User.skill_learn) == func.lower(current_user.skill_teach),
       User.id != current_user.id
    ).all()


    return render_template("dashboard.html", user=current_user, matches=matches)

@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
def chat(user_id):
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    other_user = User.query.get(user_id)

    if not other_user:
        flash("User not found!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        content = request.form['content']
        if content.strip():
            new_msg = Message(
                sender_id=current_user.id,
                receiver_id=other_user.id,
                content=content
            )
            db.session.add(new_msg)
            db.session.commit()
            flash("Message sent!", "success")

    # Fetch chat history (ordered by time)
    chat_history = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    return render_template("chat.html",
                           current_user=current_user,
                           other_user=other_user,
                           messages=chat_history)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
