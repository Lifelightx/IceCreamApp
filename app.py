from flask import Flask,render_template,request,url_for,session,redirect,flash,jsonify,json
import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
import MySQLdb
import time
from werkzeug.security import generate_password_hash,check_password_hash

load_dotenv()

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(),'static','uploads')
app.config["MAX_CONTENT_LENGTH"] =  1024 * 1024*4;
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
    if 'email' and 'name' in session:
        user = {"email": session['email'], "name": session['name']}
        return render_template('about.html',user=user)
    return render_template('about.html', user=None)
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
    
@app.route('/add', methods=['POST', 'GET'])
def add_iceCreams():
    if request.method == 'POST':
        name = request.form['name']
        price = int(request.form['price'])
        category = request.form['category']
        desc = request.form['description']
        image = request.files['image']
        
        image_name = secure_filename(image.filename)
        unique_img_name = f"{time.time()}_{image_name}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'],unique_img_name)
        image.save(image_path)
        conn = db_connect()
        cursor = conn.cursor()
        try:
            querry = "insert into ICECREAMS(name,descriptions,category,image_name,price)values(%s,%s,%s,%s,%s)"
            cursor.execute(querry,(name,desc,category,unique_img_name,price))
            conn.commit()
        except Exception as e:
            flash(f"{e}",'danger')
            conn.rollback()
    return render_template('addPage.html')

@app.route('/menu')
def menu():
    if 'email' not in session:
        return redirect('/')
    else:
        conn = db_connect()
        cursor = conn.cursor()
        try:
            querry = "select * from ICECREAMS"
            cursor.execute(querry)
            iceCreams = cursor.fetchall()
        # for i in iceCreams:
        #     print(i)
            return render_template('menu.html', iceCreams=iceCreams)
        except Exception as e:
            flash(f"{e}",'danger')
        finally:
            conn.close()
@app.route('/addToCart', methods=['POST'])
def addToCart():
    data = request.json
    querry = "select * from users where email = %s"
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(querry,(session.get('email'),))
        row = cursor.fetchone()
        cart = json.loads(row[4]) if row[4] else []
        if data not in cart:
            cart.append(data)
        else:
            return jsonify({"message":"Item Alread in cart.","status":"warning"})
        updated_cart = json.dumps(cart)
        updateQuerry = "update users set cart = %s where email=%s "
        cursor.execute(updateQuerry,(updated_cart,session.get('email')))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"message":"Item does not added","error":f"{e}", "status":"error"})
    return jsonify({"message":"Item added successfully", "status":"success"})

@app.route('/view_cart')
def view_cart():
    conn = db_connect()
    cursor = conn.cursor()
    querry = "select cart from users where email = %s"
    cursor.execute(querry,(session.get('email'),))
    row = cursor.fetchone()
    cart = json.loads(row[0]) if row[0] else []  
    total_sum = sum(float(item['price']) for item in cart)        
    return render_template('cart.html', cart=cart,total_sum=total_sum) 

@app.route('/remove_item')
def remove_Item():
    id = request.args.get('id')
    conn = db_connect()
    cursor = conn.cursor()

    # Fetch the current cart for the user
    query = "SELECT cart FROM users WHERE email = %s"
    cursor.execute(query, (session.get('email'),))
    row = cursor.fetchone()

    # Load the cart and remove the item
    cart = json.loads(row[0]) if row[0] else []
    updated_cart = [item for item in cart if item.get('id') != id]

    # Save the updated cart back to the database
    query = "UPDATE users SET cart = %s WHERE email = %s"
    cursor.execute(query, (json.dumps(updated_cart), session.get('email')))
    conn.commit()

    # Close connection
    cursor.close()
    conn.close()
    return redirect('/view_cart')
    



if __name__ == '__main__':
    app.run(debug=True)