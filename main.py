import pymysql
from flask import Flask, render_template, request,session,redirect

app = Flask(__name__)
app.secret_key="lostandfound"

conn = pymysql.connect(host="localhost",db="lost_and_found",user="root",password="root")
cursor = conn.cursor()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/adminLogin")
def adminLogin():
    return render_template("adminLogin.html")


@app.route("/userLogin")
def userLogin():
    return render_template("userLogin.html")

@app.route("/admin_login_action",methods=['post'])
def admin_login_action():
    userName = request.form.get("userName")
    password = request.form.get("password")
    if userName=="admin" and password =="admin":
        session['role']='admin'
        return render_template("admin_home.html")
    else:
      return render_template("message.html",message="Invalid Login Details",color='alert danger')


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/user_reg")
def user_reg():
    return render_template("user_reg.html")

@app.route("/user_reg_action",methods=['post'])
def user_reg_action():
    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    password = request.form.get("password")
    count = cursor.execute("select * from Users where phone='"+str(phone)+"' or email='"+str(email)+"'")
    if count>0:
        return render_template("message.html",message="Duplicate User Details",color="alert danger")
    cursor.execute("insert into Users (name,email,phone,password) values ('"+str(name)+"','"+str(email)+"','"+str(phone)+"','"+str(password)+"')")
    conn.commit()
    return render_template("message.html", message="User Registered Successfully", color="alert success")


@app.route("/user_login_action",methods=['post'])
def user_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    count = cursor.execute("select * from Users where email='"+str(email)+"' and password='"+str(password)+"'")
    if count>0:
        user = cursor.fetchone()
        session['role']='user'
        session['user_id'] = user[0]
        return render_template('user_home.html')
    else:
        return render_template("message.html",message="Invalid Login Details",color='alert danger')


@app.route("/user_home")
def user_home():
    return render_template("user_home.html")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")

@app.route("/locations")
def locations():
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    return render_template("locations.html",locations=locations)

@app.route("/add_location_action",methods=['post'])
def add_location_action():
    location_name =  request.form.get("location_name")
    building_name =  request.form.get("building_name")
    room_no =  request.form.get("room_no")
    details =  request.form.get("details")
    count = cursor.execute("select * from Locations where location_name='"+str(location_name)+"'")
    if count>0:
        return render_template("message.html",message="Location "+str(location_name)+" Exists",color="alert danger")

    cursor.execute("insert into Locations (location_name,building_name,room_no,details) values ('"+str(location_name)+"','"+str(building_name)+"','"+str(room_no)+"','"+str(details)+"')")
    conn.commit()
    return redirect("/locations")


app.run(debug=True)