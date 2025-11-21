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
    user_id = session['user_id']

    # Get lost items of user that are matched
    cursor.execute("""
           SELECT l.lost_item_id, l.item_name, l.description, l.lost_date, loc.location_name
           FROM Lost_Items l
           JOIN Locations loc ON l.location_id = loc.location_id
           WHERE l.user_id=%s AND l.status='Matched'
           ORDER BY l.lost_item_id DESC
       """, (user_id,))
    matched_lost_items = cursor.fetchall()

    # Get found items of user that are matched
    cursor.execute("""
           SELECT f.found_item_id, f.item_name, f.description, f.found_date, loc.location_name
           FROM Found_Items f
           JOIN Locations loc ON f.location_id = loc.location_id
           WHERE f.finder_id=%s AND f.status='Matched'
           ORDER BY f.found_item_id DESC
       """, (user_id,))
    matched_found_items = cursor.fetchall()

    return render_template("user_matched_dashboard.html",
                           matched_lost_items=matched_lost_items,
                           matched_found_items=matched_found_items)


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

@app.route("/lost_items")
def lost_items():
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    cursor.execute("""
           SELECT l.*, loc.location_name 
           FROM Lost_Items l
           JOIN Locations loc ON l.location_id = loc.location_id
           ORDER BY l.lost_item_id DESC
       """)
    lost_items = cursor.fetchall()
    return render_template("lost_items.html",locations=locations,lost_items=lost_items)



@app.route("/found_items")
def found_items():
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    cursor.execute("""
           SELECT f.*, loc.location_name 
           FROM Found_Items f
           JOIN Locations loc ON f.location_id = loc.location_id
           ORDER BY f.found_item_id DESC
       """)
    found_items = cursor.fetchall()
    return render_template("found_items.html",locations=locations,found_items=found_items)




#
# @app.route("/add_found_item_action",methods=['post'])
# def add_found_item_action():
#     item_name = request.form.get("item_name")
#     found_date = request.form.get("found_date")
#     location_id = request.form.get("location_id")
#     description = request.form.get("description")
#     finder_id  = session['user_id']
#     cursor.execute("insert into Found_Items (item_name,found_date,location_id,description,finder_id) values ('"+str(item_name)+"','"+str(found_date)+"','"+str(location_id)+"','"+str(description)+"','"+str(finder_id)+"')")
#     conn.commit()
#     return render_template("message.html",message="Found Item Added",color="alert primary")


@app.route("/add_found_item_action", methods=['post'])
def add_found_item_action():
    item_name = request.form.get("item_name")
    found_date = request.form.get("found_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    finder_id = session['user_id']

    # Insert found item
    cursor.execute("""
        INSERT INTO Found_Items (item_name, found_date, location_id, description, finder_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (item_name, found_date, location_id, description, finder_id))
    conn.commit()

    found_item_id = cursor.lastrowid

    # Check for matching lost items
    cursor.execute("""
        SELECT lost_item_id, item_name, lost_date, user_id
        FROM Lost_Items
        WHERE location_id=%s AND item_name LIKE %s AND status='Lost'
    """, (location_id, f"%{item_name}%"))
    matches = cursor.fetchall()

    match_info = ""

    for match in matches:
        lost_item_id = match[0]
        user_id = match[3]

        # Update status to 'matched' for both items
        cursor.execute("UPDATE Found_Items SET status='matched' WHERE found_item_id=%s", (found_item_id,))
        cursor.execute("UPDATE Lost_Items SET status='matched' WHERE lost_item_id=%s", (lost_item_id,))
        conn.commit()

        match_info += f"Match Found! Lost Item ID: {lost_item_id} (Owner ID: {user_id})<br>"

    if not match_info:
        match_info = "No matches found yet."

    return render_template("message.html", message="Found Item Added.<br>" + match_info, color="alert-primary")


# @app.route("/add_lost_item",methods=['post'])
# def add_lost_item():
#     item_name = request.form.get("item_name")
#     lost_date = request.form.get("lost_date")
#     location_id = request.form.get("location_id")
#     description = request.form.get("description")
#     user_id  = session['user_id']
#     cursor.execute("insert into Lost_Items (item_name,lost_date,location_id,description,user_id) values ('"+str(item_name)+"','"+str(lost_date)+"','"+str(location_id)+"','"+str(description)+"','"+str(user_id)+"')")
#     conn.commit()
#     return render_template("message.html",message="Lost Item Added",color="alert primary")


@app.route("/add_lost_item", methods=['post'])
def add_lost_item():
    item_name = request.form.get("item_name")
    lost_date = request.form.get("lost_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    user_id = session['user_id']

    # Insert lost item
    cursor.execute("""
        INSERT INTO Lost_Items (item_name, lost_date, location_id, description, user_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (item_name, lost_date, location_id, description, user_id))
    conn.commit()

    lost_item_id = cursor.lastrowid

    # Check for matching found items
    cursor.execute("""
        SELECT found_item_id, item_name, found_date, finder_id
        FROM Found_Items
        WHERE location_id=%s AND item_name LIKE %s AND status='Found'
    """, (location_id, f"%{item_name}%"))
    matches = cursor.fetchall()

    match_info = ""

    for match in matches:
        found_item_id = match[0]
        finder_id = match[3]

        # Update status to 'matched' for both lost and found item
        cursor.execute("""
            UPDATE Lost_Items SET status=%s WHERE lost_item_id=%s
        """, ("matched", lost_item_id))
        conn.commit()
        cursor.execute("""
                   UPDATE Found_Items SET status=%s WHERE found_item_id=%s
               """, ("matched", found_item_id))
        conn.commit()
        conn.commit()

        match_info += f"Match Found! Found Item ID: {found_item_id} (Finder ID: {finder_id})<br>"

    if not match_info:
        match_info = "No matches found yet."

    return render_template("message.html", message="Lost Item Added.<br>" + match_info, color="alert-primary")


@app.route("/edit_lost_item")
def edit_lost_item():
    lost_item_id = request.args.get("lost_item_id")
    cursor.execute("select * from Lost_Items where lost_item_id='"+str(lost_item_id)+"'")
    Lost_Item = cursor.fetchone()
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    return render_template("edit_lost_item.html",Lost_Item=Lost_Item,locations=locations,lost_item_id=lost_item_id)




@app.route("/edit_found_item")
def edit_found_item():
    found_item_id = request.args.get("found_item_id")
    cursor.execute("select * from Found_Items where found_item_id='"+str(found_item_id)+"'")
    Found_Item = cursor.fetchone()
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    return render_template("edit_found_item.html",Found_Item=Found_Item,locations=locations,found_item_id=found_item_id)




@app.route("/edit_lost_item_action",methods=['post'])
def edit_lost_item_action():
    lost_item_id = request.form.get("lost_item_id")
    item_name = request.form.get("item_name")
    lost_date = request.form.get("lost_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    cursor.execute("update Lost_Items set item_name='"+str(item_name)+"',lost_date='"+str(lost_date)+"',location_id='"+str(location_id)+"',description='"+str(description)+"' where lost_item_id='"+str(lost_item_id)+"'")
    conn.commit()
    return redirect("/lost_items")


@app.route("/edit_found_item_action",methods=['post'])
def edit_found_item_action():
    found_item_id = request.form.get("found_item_id")
    item_name = request.form.get("item_name")
    found_date = request.form.get("found_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    cursor.execute("update Found_Items set item_name='"+str(item_name)+"',found_date='"+str(found_date)+"',location_id='"+str(location_id)+"',description='"+str(description)+"' where found_item_id='"+str(found_item_id)+"'")
    conn.commit()
    return redirect("/found_items")


@app.route("/delete_lost_item")
def delete_lost_item():
    lost_item_id = request.args.get("lost_item_id")
    cursor.execute("delete from Lost_Items where lost_item_id='"+str(lost_item_id)+"'")
    conn.commit()
    return redirect("/lost_items")

@app.route("/delete_found_item")
def delete_found_item():
    found_item_id = request.args.get("found_item_id")
    cursor.execute("delete from Found_Items where found_item_id='"+str(found_item_id)+"'")
    conn.commit()
    return redirect("/found_items")




app.run(debug=True)