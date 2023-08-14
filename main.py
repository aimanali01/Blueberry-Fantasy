from flask import Flask, render_template,session, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import Pagination
from datetime import datetime
import json
from base64 import b64encode
import math

bcrypt = Bcrypt()
current_datetime = datetime.now()

with open('config.json', 'r') as c:
    parameters = json.load(c)["parameters"]
   
local_server = False    
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.secret_key = 'code-is-life' 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'blueberryfantasy'

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['prod_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email_adres = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Add_blog(db.Model):   
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    tags = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.LargeBinary(12582912), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('register.sno'), nullable=False)
    
    user = db.relationship('Register', backref='blogs')
    
class Register(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(80), unique=False, nullable=False)
    lname = db.Column(db.String(80), unique=False, nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password_to_check):
        return bcrypt.check_password_hash(self.password, password_to_check)
    
class Comments(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    cname = db.Column(db.String(80), unique=False, nullable=False)
    yemail = db.Column(db.String(20), nullable=False)
    response = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('add_blog.sno'), nullable=False)
    
    user = db.relationship('Add_blog', backref='blogs')
    
@app.route("/")
def home():
    logged_in = 'user_id' in session and session['user_id'] is not None

    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)    
        
    blogs_query = Add_blog.query.paginate(page=page, per_page=int(parameters['no_of_blogs']))
    blogs = blogs_query.items
    prev = "#"
    next = "#"
    if blogs_query.has_prev:
        prev = f"/?page={blogs_query.prev_num}"
    if blogs_query.has_next:
        next = f"/?page={blogs_query.next_num}"
    
    blog_images = {blog.sno: b64encode(blog.img_file).decode() for blog in blogs}
    
    return render_template('index.html', parameters=parameters, add_blog=blogs, blog=blogs, blog_images=blog_images, prev=prev, next=next, logged_in=logged_in)



@app.route('/search', methods=['POST'])
def search():
    logged_in = 'user_id' in session and session['user_id'] is not None
    if request.method == 'POST':
        add_blog = Add_blog.query.filter_by().all()
        query = request.form['query'].lower()
        results = [blog for blog in add_blog if query in blog.title.lower() or query in blog.content.lower()]
        result_images = {}
        for result in results:
            image = b64encode(result.img_file).decode()
            result_images[result.sno] = image
            image = result_images
    blog = Add_blog.query.all()
    return render_template('search_results.html', results=results, blog=blog, result_images=result_images, logged_in=logged_in)
   
   
    
@app.route("/post/<string:sno>", methods = ['GET', 'POST'])
def post_route(sno):
    logged_in = 'user_id' in session and session['user_id'] is not None
    blog = Add_blog.query.filter_by(sno=sno).first()
    post_id = blog.sno
    comments = Comments.query.filter_by(post_id=post_id).all()
    image = b64encode(blog.img_file).decode()
    
    if request.method == 'POST':
        cname = request.form.get('cname')
        yemail = request.form.get('yemail')
        response = request.form.get('response')
        post_id = blog.sno
        comment = Comments(cname=cname, yemail=yemail, response=response, date=datetime.now(), post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        blog = Add_blog.query.filter_by().first() 
        return redirect('/post/' + sno)
    return render_template('post-image.html',blog=blog, parameters=parameters, comments=comments, img=image, logged_in=logged_in)



@app.route("/register/", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone_num = request.form.get('phone_num')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = Register.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered. Please log in.', 'error')
            return redirect(url_for('login'))

        new_user = Register(email=email, password=password, phone_num=phone_num, fname=fname, lname=lname, date=datetime.now())
        # new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. Please log in.', 'success')
        return redirect('/login')

    return render_template('register.html', parameters=parameters)



@app.route("/add_blogs/", methods = ['GET', 'POST'])
def addblog():
    logged_in = 'user_id' in session and session['user_id'] is not None
    if request.method == 'POST':
        if session['logged_in'] == True:
            title = request.form.get('title')
            category = request.form.get('category')
            tags = request.form.get('tags')
            content = request.form.get('editor1')
            image = request.files.get('img_file')
            user_id = session['user_id']
            image_data = image.read() 
            blog = Add_blog(title=title, category=category, tags=tags, content=content, date=datetime.now(), img_file=image_data, user_id=user_id)
            db.session.add(blog)
            db.session.commit()
        return redirect('/dashboard/')
    blog = Add_blog.query.filter_by().all()
    return render_template('add_blog.html', parameters=parameters, logged_in=logged_in, blog=blog)



@app.route("/contact" ,methods = ['GET', 'POST'])
def contact():
    logged_in = 'user_id' in session and session['user_id'] is not None
    if request.method == 'POST':
        name = request.form.get('name')
        email_adres = request.form.get('email_adres')
        msg = request.form.get('msg')
        entry = Contact(name=name, email_adres=email_adres, msg=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()   
    return render_template('page-contact.html', parameters=parameters, logged_in=logged_in)



@app.route("/dashboard/")
def dashboard():
    sno = session['user_id']
    user = Register.query.get(sno)
    add_blog = Add_blog.query.filter_by(user_id=user.sno).all()
    return render_template('dashboard.html', user=user, add_blog=add_blog)



@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    logged_in = 'user_id' in session and session['user_id'] is not None
    blog = Add_blog.query.filter_by(sno=sno).first()
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        tags = request.form.get('tags')
        content = request.form.get('editor1')
        img = request.files.get('img_file')
        user_id = session['user_id']
        
        blog = Add_blog.query.filter_by(sno=sno).first()
        blog.sno = sno
        blog.title = title
        blog.category = category
        blog.tags = tags
        blog.content = content

        if img.filename != '':  
            img_path = 'static/img/'
            with open(img_path + img.filename, 'rb') as file:
                blog.img_file = file.read()
        elif img.filename is None:
            image = request.files.get('image')  
            blog.img_file = image

        db.session.commit()
        return redirect('/dashboard/')
    img = request.files.get('img_file')
    return render_template('edit.html', parameters=parameters, sno=sno, blog=blog, logged_in=logged_in, img=img)



@app.route("/delete/<string:sno>" , methods=['GET', 'POST'])
def delete(sno):
    blog = Add_blog.query.filter_by(sno=sno).first()
    if blog:
        db.session.delete(blog)
        db.session.commit()
    return redirect("/dashboard/")   


@app.route("/post/<string:sno>/delete/<string:id>" , methods=['GET','POST'])
def deleteComment(sno, id):
    comment = Comments.query.filter_by(sno=id).first()
    if comment:
        db.session.delete(comment)
        db.session.commit()
    return redirect('/post/' + sno)


@app.route("/login/", methods=['GET', 'POST'])
def login():
    if 'user_id' in session and session['user_id'] is not None:
        return redirect('/dashboard/')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = Register.query.filter_by(email=email, password=password).first()

        if user:
            session['logged_in'] = True
            session['user_id'] = user.sno
            flash('Logged in successfully!', 'success')
            return redirect('/dashboard/')

        flash('Invalid email or password. Please try again.', 'error')

    return render_template('login.html', parameters=parameters)



@app.route("/logout/")
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


@app.after_request
def add_cache_control(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response  

# app.run(debug=True)