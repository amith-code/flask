from flask import Flask, render_template,request,session,redirect,make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import math
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'super-secret-key'

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app.config['UPLOAD_FOLDER']= params['upload_location']

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['MAIL_USERNAME'],
    MAIL_PASSWORD=params['MAIL_PASSWORD'],
)
mail=Mail(app)
local_server=True
if(local_server==True):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_uri']
db = SQLAlchemy(app)

class Contact(db.Model):
    sno= db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20),  nullable=False)
    ph_no = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(20),  nullable=False)
    msg = db.Column(db.String(80), nullable=False)
    date_time = db.Column(db.String(12),  nullable=False)

class Post(db.Model):
    sno= db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20),  nullable=False)
    slug = db.Column(db.String(20),  nullable=False)
    content = db.Column(db.Integer, primary_key=True)
    tagline = db.Column(db.Integer, primary_key=True)
    posted_by = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(12),  nullable=False)
    img = db.Column(db.String(25), nullable=False)

@app.route("/")
def home():
    posts=Post.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    print(page)
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    return render_template('index.html',params=params,posts=posts,next=next,prev=prev)


@app.route("/about",methods=["GET","POST"])
def about():

    return render_template('index.html',params=params)
@app.route("/logout")
def logout():
    session.pop('user')
    response = make_response(redirect('/dashboard'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response



@app.route("/addpost",methods=["GET","POST"])
def addpost():
    if (request.method=='POST'):
        posttitle=request.form.get('post-title')
        postcontent=request.form.get('post-content')
        posttagline=request.form.get('post-tagline')

        entry=Post(title=posttitle,content=postcontent,tagline=posttagline,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        print("arjun")
    return render_template('addpost.html',params=params)


@app.route("/editpost/<string:sno>",methods=["GET","POST"])
def editpost(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Post.query.filter_by(sno=sno).first()
        if(request.method=='POST'):
            title=request.form.get('title')
            tagline=request.form.get('tagline')
            content=request.form.get('content')
            post=Post.query.filter_by(sno=sno).first()
            print(post)
            if title:
                post.title = title
            if tagline:
                post.tagline = tagline
            if content:
                post.content = content
            try:
                db.session.commit()
                return redirect('/editpost/'+sno)
            except:
                return "there was a problem"

        return render_template('editpost.html',params=params,post=post)

@app.route("/delete/<string:sno>",methods=["GET","POST"])
def deletepost(sno):
    posts = Post.query.filter_by(sno=sno).first()
    print(posts)
    db.session.delete(posts)
    db.session.commit()

    return redirect('/dashboard')

@app.route("/dashboard",methods=["GET","POST"])
def dashboard():

    if 'user' in session and session['user']==params['admin_user'] :
        posts = Post.query.all()
        response = make_response(render_template('dashboard.html',params=params,posts=posts))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response



    if(request.method=='POST'):
        user_name = request.form.get('username')
        pas= request.form.get('password')
        session['user'] = user_name
        print(type(session['user']))

        print(type(request.form.get('password')))
        print(type(params['admin_password']))
        if( user_name==params['admin_user'] and pas==params['admin_password']):
            print("arjun")
            posts = Post.query.all()
            return render_template('/dashboard.html',params=params,posts=posts)


    print("akhil")
    return render_template('login.html', params=params)

@app.route("/upload",methods=["GET","POST"])
def uploadfile():
    if 'user' in session and session['user']==params['admin_user'] :
        if request.method == 'POST' :
            f=request.files['filename']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded successfully!"







@app.route("/contact",methods=["GET","POST"])
def contact():

    if (request.method=='POST'):
        name=request.form.get('name')
        eml=request.form.get('email')
        phone=request.form.get('ph_no')
        message=request.form.get('msg')
        entry=Contact(name=name,email=eml,ph_no=phone,msg=message,date_time=datetime.now())
        db.session.add(entry)
        db.session.commit()

        mail.send_message(subject="New message from " + name,
                          sender=eml,
                          recipients=[params['MAIL_USERNAME']],
                          body=message + "\n" + phone)

    return render_template('contact.html',params=params)
@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post=Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)



app.run(debug=True)

