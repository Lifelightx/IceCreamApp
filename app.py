from flask import Flask,render_template,request,url_for,session,redirect,flash
import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import MySQLdb
from werkzeug.security import generate_password_hash,check_password_hash

load_dotenv()

app = Flask(__name__)

app.secret_key = 'MysecretKyeisNotdefinedSO5nb'

def db_connect():
    return MySQLdb.connect(host='sql12.freesqldatabase.com', user='sql12756218',database='sql12756218', password='iBYTMrg9Jc')

@app.route('/')
def home():
    if 'email' and 'name' in session:
        user = {"email": session['email'], "name": session['name']}
        return render_template('index.html',user=user)
    return render_template('index.html',user=None)

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
    return render_template('contact.html')



@app.route('/request_otp', methods=['POST', 'GET'])
def request_otp():
    if request.method == "POST":
        email = request.form.get('email')
        if email is not None:
            otp = random.randint(100000,999999)
            session['otp'] = otp
            session['email'] = email
            body = f'''Your One Time Password is : {otp}'''
            msg = MIMEText(body)
            fromAddr = os.getenv("EMAIL")
            toAddr = email.strip()
            msg['From'] = fromAddr
            msg['To'] = toAddr
            msg['Subject'] = 'OTP verification on Galcier Goodness' 
            server = smtplib.SMTP('smtp.gmail.com',587)
            server.starttls()
            try:
                server.login(fromAddr, os.getenv("APP_PASSWORD"))
                server.send_message(msg)
                flash("OTP Sent to your mail",'success')
                server.quit()
            except Exception as e:
                flash("There was something error while sending OTP", 'danger')
                return f"{e}";
            return render_template('verify_otp.html', email=email)
        else:
            return redirect('/request_otp')  
    return render_template('reqotp.html')      
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    if request.method == "POST":
        user_otp = request.form['otp']
        print(user_otp)
        if user_otp == str(session['otp']):
            print("Matched........")
            session.pop('otp')
            session['user_otp'] = user_otp
            return redirect('/signup')
        return redirect('/request_otp')
    return "Sorry, you are not allowed to"
    

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    
    if 'email' not in session or 'user_otp' not in session:
        return redirect('/')
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        hashPassword = generate_password_hash(password)
        conn = db_connect()
        cursor = conn.cursor()
        try:
            querry = "insert into users (name, email, password) values (%s, %s, %s)"
            cursor.execute(querry,(name,session.get('email'),hashPassword))
            conn.commit()
            if 'email' in session:
                session.pop('email', None)
            return redirect('/login')
        except Exception as e:
            conn.rollback()
            flash("Error while signing up", 'danger')
            return f"{e}"
        finally:
            conn.close()
    return render_template('signup.html',email = session['email'])

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = db_connect()
        try:
            cursor = conn.cursor()
            querry = "select * from users where email=%s"
            cursor.execute(querry, (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user[3], password):
                session['email'] = user[2]
                session['name'] = user[1]
                return redirect('/')
            else:
                flash('Invalid email or password', 'danger')
        except Exception as e:
            flash("Error while login", 'danger')
            return f"{e}"
        finally:
            conn.close()
    return render_template('login.html')
@app.route('/logout')

def logout():
    session.pop('email', None)
    session.pop('name', None)
    return redirect('/')     
    

if __name__ == '__main__':
    app.run(debug=True)