from flask import *
from flask_sqlalchemy import *
from flask_mail import *
from datetime import datetime
import math
from werkzeug import *
import os
import json
with open("config.json", "r") as read_file:
    params = json.load(read_file)["params"]

app=Flask(__name__)
app.secret_key = "abcgbu"
app.config['UPLOAD_FOLDER']=params["upload_location"]
app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=465,
        MAIL_USE_SSL= True,
        MAIL_USERNAME = params["gmail_user"],
        MAIL_PASSWORD= params["gmail_password"],
)
mail=Mail(app)
local_server=True
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
    app.config['SECRET_KEY'] = "abcgbu"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    phone_num = db.Column(db.String (12), nullable=False)
    msg = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    posted_by = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(20), nullable=False)
    subtitle = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String (120), nullable=False)
    img_file = db.Column(db.String(50), nullable=True)
    date = db.Column(db.String(20), nullable=True)


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Posts.query.paginate(page=page, per_page=params["no_of_post"])

    return render_template('index.html', params=params, posts=posts )

@app.route('/contact', methods=['GET', 'POST'])
def contact():
   if request.method == 'POST':

      name = request.form['name']
      email = request.form['email']
      phone = request.form['phone']
      message = request.form['message']

      result = Contacts(name=name ,email=email ,phone_num=phone, msg=message , date=datetime.now())

      db.session.add(result)
      db.session.commit()

      mail.send_message('New Message Recived From ' + name, sender=email,
                        recipients= [params["gmail_user"]],
                        body= message + "\n" + phone

                        )
      flash('Message Sent Successfully...!! Thanks for contacting.')
      return render_template('contact.html', params=params)
   else:
      return render_template('contact.html', params=params)

@app.route('/post/<string:post_slug>', methods=['GET', 'POST'])
def sample_post(post_slug):

    posts=Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params, posts=posts)


@app.route('/edit_blog/<string:sno>', methods=['GET','POST'] )
def edit(sno):
     if ('user' in session and session['user'] == params['admin_uname']):

        if request.method == 'POST':
            name = request.form['name']
            title = request.form['title']
            subtitle = request.form['subtitle']
            slug = request.form['slug']
            content = request.form['content']
            image = request.form['img']
            date = datetime.now()

            post=Posts.query.filter_by(sno=sno).first()

            post.posted_by=name
            post.title=title
            post.subtitle = subtitle
            post.slug = slug
            post.content = content
            post.date=date
            post.img_file=image
            db.session.commit()
            return  redirect('/post_show')

        post=Posts.query.filter_by(sno=sno).first()

        return render_template('edit_blog.html', params=params, sno=sno, post=post)
     else:
         return render_template('login.html', params=params)


@app.route('/add_blog', methods=['GET','POST'] )
def add_blog():
     if ('user' in session and session['user'] == params['admin_uname']):

        if request.method == 'POST':
            name = request.form['name']
            title = request.form['title']
            subtitle = request.form['subtitle']
            slug = request.form['slug']
            content = request.form['content']
            image = request.form['img']
            date = datetime.now()

            post = Posts(posted_by=name, title=title, subtitle=subtitle, slug=slug, content=content,img_file=image, date=date)
            db.session.add(post)
            db.session.commit()
            flash('New blog added successfully in database...!!')
            return redirect('/add_blog')

        #=Posts.query.filter_by().first()

        return render_template('add_blog.html', params=params )
     else:
         return render_template('login.html', params=params)

@app.route('/about')
def about():
    return render_template('about.html', params=params)

@app.route('/post_show', methods=['GET', 'POST'] )
def post_show():
    
    if ('user' in session and session['user']==params['admin_uname'] ):
        posts = Posts.query.all()

        return render_template('post_show.html', params=params, posts=posts)
    else:
        return render_template('login.html', params=params)

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')
        return render_template('login.html',  params=params)
    else:
        #return '<p>user already logged out</p>'
        return render_template('index.html')

@app.route('/delete/<string:sno>', methods=['GET','POST'] )
def delete_post(sno):
    if ('user' in session and session['user']==params['admin_uname'] ):
        delete =Posts.query.filter_by(sno=sno).first()
        db.session.delete(delete )
        db.session.commit()
        return redirect('/post_show')
    else:
        return render_template('login.html', params=params)


# @app.route('/upload', methods=['GET', 'POST'])
# def upload():
#     if ('user' in session and session['user']==params['admin_uname'] ):
#
#         if request.method == 'POST':
#
#             f=request.files['file1']
#             f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.file1)))
#             return "uploaded"

@app.route('/message_show', methods=['GET', 'POST'])
def message_show():
    if ('user' in session and session['user'] == params['admin_uname']):
        msgs = Contacts.query.all()

        return render_template('message_show.html', params=params, msgs=msgs)
    else:
        return render_template('login.html', params=params)

@app.route('/delete_msg/<string:sno>', methods=['GET','POST'] )
def delete_msg(sno):
    if ('user' in session and session['user']==params['admin_uname'] ):
        delete =Contacts.query.filter_by(sno=sno).first()
        db.session.delete(delete )
        db.session.commit()
        return redirect('/message_show')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user']==params['admin_uname'] ):
        #posts = Posts.query.all()

        return render_template('dashboard.html', params=params)

    if request.method=='POST':
        username=request.form['uname']
        userpass=request.form['pass']

        if(username == params['admin_uname'] and userpass == params['admin_pass']):
            session['user']=username
            #posts=Posts.query.all()
            return render_template('dashboard.html', params=params)
        else:
            flash('Sorry...!! Incorrect password')

    return render_template('login.html', params=params)

if __name__ == "__main__":
    app.run( debug = True)
