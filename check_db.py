from app import app, db, User

# Use the Flask app context so db works
with app.app_context():
    users = User.query.all()
    if users:
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Teaches: {u.skill_teach}, Learns: {u.skill_learn}")
    else:
        print("No users found in the database.")
