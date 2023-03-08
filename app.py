
from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import pymysql
import json
from math import ceil

local_server =True
with open('config.json','r') as c:
    params = json.load(c)['params']


app = Flask(__name__)

# create the extension
db = SQLAlchemy()

if local_server:
# configure the SQLite database, relative to the app instance folder
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db.init_app(app)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['password']
)

app.secret_key = 'mykey'
mail = Mail(app)
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Definig the model : table
class contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50),nullable=False)
    phone = db.Column(db.Integer,nullable=False)
    message = db.Column(db.String(200),nullable=False)
    date = db.Column(db.String(12),nullable=True)

class blogs(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50),nullable=False)
    content = db.Column(db.String(600),nullable=False)
    date = db.Column(db.String(12),nullable=True)

@app.route("/")
def home():
    posts = blogs.query.filter_by().all()
    last =  ceil(len(posts)/int(params['no_of_posts']))
   
    # [0:params['no_of_posts']]
    # Pagination logic
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1

    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    
    if(page == 1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page == last):
        next = "#"
        prev = "/?page="+str(page-1)
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)


    return render_template("index.html",params = params,posts = posts,prev = prev,next = next)


@app.route("/about")
def about():
    return render_template("about.html",params = params)

@app.route("/post/<string:post_slug>",methods = ['GET'])
def post_route(post_slug):
    post = blogs.query.filter_by(slug = post_slug).first()
    return render_template("post.html",params = params,post = post)

@app.route("/contact", methods=["GET", "POST"])
def contacts():
    print(request.method)
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")
       
        entry = contact(name = name,email = email,phone = phone,message = message,date = datetime.now())
        db.session.add(entry)
        db.session.commit()

        # mail.send_message('new message from blog',
        #                   sender = name,
        #                   recipients = [params['gmail_user']],
        #                   body = message + '\n' + phone)

        
    
    return render_template("contact.html",params = params)

@app.route('/dashboard',methods = ['GET','POST'])
def dashboard():
    posts = blogs.query.filter_by().all()

    if ("user" in session and session['user'] == params['admin_user']):
        return render_template('dashboard.html', params = params,posts = posts)
    if request.method == "POST":
        uname = request.form.get('name')
        password = request.form.get('password')

        if (uname == params['admin_user']) and (password == params['admin_password']):
            # set the session variable
            session['user'] = uname
            return render_template('dashboard.html',params = params,posts = posts)

    
    return render_template('admin.html',params= params)

@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if ("user" in session and session['user'] == params['admin_user']):
        if(request.method == "POST"):
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()
            print(title,slug)
            

            if sno == "0":
                post = blogs(title = title,slug = slug,content = content,date=date)
                db.session.add(post)
                db.session.commit()
                print("data has been added")
                return redirect('/edit/'+sno)
           
            else:
                post = blogs.query.filter_by(sno = sno).first()
                post.title = title
                post.slug = slug
                post.content = content

                db.session.commit()
                return redirect('/edit/'+sno)
                

    post = blogs.query.filter_by(sno = sno).first()
    
    return render_template('edit.html',post = post,sno = sno)

@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if ("user" in session and session['user'] == params['admin_user']):
        post = blogs.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    
    return redirect('/dashboard')
    

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/dash-home')
def dashhome():
    return redirect('/dashboard')


app.run(debug=True)