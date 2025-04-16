from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy    
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime

import os 

app = Flask(__name__)
#secret key for the flask_login 
app.config['SECRET_KEY'] = 'your_secret_key'

#creating the database 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
#creating the login for flask-login
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

#user class creation 
class user(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    posts = db.relationship('post', backref='author', lazy=True)

    def __repr__(self):
        return f"user('{self.username}', '{self.email}')"

#Post class creation
class post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"post('{self.title}', '{self.date_posted}')"

#Comment class creation
class comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author = db.relationship('user', backref='comments')

    def __repr__(self):
        return f"comment('{self.content}', '{self.date_posted}')"

@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query", "").lower()
    results = []  # Store matched page names

    if query:
        # Loop through the "templates" directory to find matching HTML files
        for filename in os.listdir("templates"):
            if filename.endswith(".html"):
                with open(os.path.join("templates", filename), "r", encoding="utf-8") as file:
                    content = file.read().lower()
                    if query in content:
                        page_name = filename.replace(".html", "")
                        results.append(page_name)

    return render_template("search_results.html", results=results, query=query)



@app.route('/AboutUs')
def AboutUs():
    return render_template('AboutUs.html')

@app.route('/research')
def research():
    return render_template('research.html')

@app.route('/research-overview')
def researchoverview():
    return render_template('research-overview.html')

@app.route('/eastdurhampark')
def eastdurhampark():
    return render_template('eastdurhampark.html')

@app.route('/eastendpark')
def eastendpark():
    return render_template('eastendpark.html')

@app.route('/lyonpark')
def lyonpark():
    return render_template('lyonpark.html')

@app.route('/northgatepark')
def northgatepark():
    return render_template('northgatepark.html')

@app.route('/walltownpark')
def walltownpark():
    return render_template('walltownpark.html')

@app.route('/test_db')
def test_db():
    users = user.query.all()
    return "<br>".join([f"{user.id}: {user.username} - {user.email}" for user in users])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Create a new user and add to the database
        new_user = user(username=username, email=email, password=password)  
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', '/success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in!", '/info')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find user by username
        found_user = user.query.filter_by(username=username).first()

        if found_user and found_user.password == password:  
            login_user(found_user)
            flash('Login successful!', '/success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', '/danger')

    return render_template('login.html')

# Logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', '/info')
    return redirect(url_for('login'))

# Takes you back to the Login
@app.route('/dashboard')
@login_required
def dashboard():
    
    f"Welcome {current_user.username}! <br><a href='/logout'>Logout</a>"
    return render_template('login.html')

# Page for blog posts
@app.route('/blog')
def blog():
    posts = post.query.order_by(post.date_posted.desc()).all() 
    return render_template('blog.html', posts=posts)

# Creating new posts only while logged in
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        new_post = post(title=title, content=content, author=current_user)  
        db.session.add(new_post)
        db.session.commit()

        flash('Your blog post has been created!', '/success')
        return redirect(url_for('blog'))

    return render_template('create_post.html')

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    blog_post = post.query.get_or_404(post_id)
    comments = comment.query.filter_by(post_id=post_id).order_by(comment.date_posted).all()

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('You must be logged in to comment.', 'danger')
            return redirect(url_for('login'))

        content = request.form['content']
        new_comment = comment(content=content, user_id=current_user.id, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
        return redirect(url_for('post_detail', post_id=post_id))

    return render_template('post_detail.html', post=blog_post, comments=comments)



if __name__ == '__main__':
    app.run(debug=True)

    
