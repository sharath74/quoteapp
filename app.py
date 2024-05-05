from flask import Flask, render_template, request, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from mongita import MongitaClientDisk
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

client = MongitaClientDisk()
quotes_db = client.quotes_db

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

users = [User(id='1', username='admin', password=bcrypt.generate_password_hash('password').decode('utf-8'))]

@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user.id == user_id:
            return user
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((user for user in users if user.username == username), None)
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('get_quotes'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/", methods=["GET"])
@app.route("/quotes", methods=["GET"])
@login_required
def get_quotes():
    quotes_collection = quotes_db.quotes_collection
    data = list(quotes_collection.find({}))
    for item in data:
        item["_id"] = str(item["_id"])
    return render_template("quotes.html", data=data)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_quote():
    if request.method == "POST":
        text = request.form['text']
        author = request.form['author']
        quotes_collection = quotes_db.quotes_collection
        quotes_collection.insert_one({"text": text, "author": author})
        return redirect(url_for('get_quotes'))
    return render_template("add_quote.html")

@app.route("/edit/<id>", methods=["GET", "POST"])
@login_required
def edit_quote(id):
    quotes_collection = quotes_db.quotes_collection
    if request.method == "POST":
        text = request.form['text']
        author = request.form['author']
        quotes_collection.update_one({"_id": ObjectId(id)}, {"$set": {"text": text, "author": author}})
        return redirect(url_for('get_quotes'))
    data = quotes_collection.find_one({"_id": ObjectId(id)})
    data["_id"] = str(data["_id"])
    return render_template("edit_quote.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
