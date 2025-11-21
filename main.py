import pymysql
from flask import Flask, render_template, request, session, redirect

app = Flask(__name__)
app.secret_key = "lostandfound"

conn = pymysql.connect(host="localhost", db="lost_and_found", user="root", password="root")
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

@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    userName = request.form.get("userName")
    password = request.form.get("password")
    if userName == "admin" and password == "admin":
        session['role'] = 'admin'
        return render_template("admin_home.html")
    return render_template("message.html", message="Invalid Login Details", color='alert danger')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/user_reg")
def user_reg():
    return render_template("user_reg.html")

@app.route("/user_reg_action", methods=['post'])
def user_reg_action():
    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    password = request.form.get("password")
    count = cursor.execute("select * from Users where phone=%s or email=%s", (phone, email))
    if count > 0:
        return render_template("message.html", message="Duplicate User Details", color="alert danger")
    cursor.execute("insert into Users (name,email,phone,password) values (%s,%s,%s,%s)", (name, email, phone, password))
    conn.commit()
    return render_template("message.html", message="User Registered Successfully", color="alert success")

@app.route("/user_login_action", methods=['post'])
def user_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    count = cursor.execute("select * from Users where email=%s and password=%s", (email, password))
    if count > 0:
        user = cursor.fetchone()
        session['role'] = 'user'
        session['user_id'] = user[0]
        return render_template('user_home.html')
    return render_template("message.html", message="Invalid Login Details", color='alert danger')

@app.route("/user_home")
def user_home():
    user_id = session['user_id']
    cursor.execute("""
        SELECT l.lost_item_id, l.item_name, l.description, l.lost_date, loc.location_name
        FROM Lost_Items l
        JOIN Locations loc ON l.location_id = loc.location_id
        WHERE l.user_id=%s AND l.status='Matched'
        ORDER BY l.lost_item_id DESC
    """, (user_id,))
    matched_lost_items = cursor.fetchall()
    cursor.execute("""
        SELECT f.found_item_id, f.item_name, f.description, f.found_date, loc.location_name
        FROM Found_Items f
        JOIN Locations loc ON f.location_id = loc.location_id
        WHERE f.finder_id=%s AND f.status='Matched'
        ORDER BY f.found_item_id DESC
    """, (user_id,))
    matched_found_items = cursor.fetchall()
    return render_template("user_home.html", matched_lost_items=matched_lost_items, matched_found_items=matched_found_items)

@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")

@app.route("/locations")
def locations():
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    return render_template("locations.html", locations=locations)

@app.route("/add_location_action", methods=['post'])
def add_location_action():
    location_name = request.form.get("location_name")
    building_name = request.form.get("building_name")
    room_no = request.form.get("room_no")
    details = request.form.get("details")
    count = cursor.execute("select * from Locations where location_name=%s", (location_name,))
    if count > 0:
        return render_template("message.html", message=f"Location {location_name} Exists", color="alert danger")
    cursor.execute("insert into Locations (location_name,building_name,room_no,details) values (%s,%s,%s,%s)",
                   (location_name, building_name, room_no, details))
    conn.commit()
    return redirect("/locations")

@app.route("/lost_items")
def lost_items():
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    cursor.execute("SELECT l.*, loc.location_name FROM Lost_Items l JOIN Locations loc ON l.location_id = loc.location_id ORDER BY l.lost_item_id DESC")
    lost_items = cursor.fetchall()
    return render_template("lost_items.html", locations=locations, lost_items=lost_items)

@app.route("/found_items")
def found_items():
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    cursor.execute("SELECT f.*, loc.location_name FROM Found_Items f JOIN Locations loc ON f.location_id = loc.location_id ORDER BY f.found_item_id DESC")
    found_items = cursor.fetchall()
    return render_template("found_items.html", locations=locations, found_items=found_items)

@app.route("/add_found_item_action", methods=['post'])
def add_found_item_action():
    item_name = request.form.get("item_name")
    found_date = request.form.get("found_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    finder_id = session['user_id']
    cursor.execute("INSERT INTO Found_Items (item_name, found_date, location_id, description, finder_id) VALUES (%s,%s,%s,%s,%s)",
                   (item_name, found_date, location_id, description, finder_id))
    conn.commit()
    found_item_id = cursor.lastrowid
    cursor.execute("SELECT lost_item_id, item_name, lost_date, user_id FROM Lost_Items WHERE location_id=%s AND item_name LIKE %s AND status='Lost'", (location_id, f"%{item_name}%"))
    matches = cursor.fetchall()
    match_info = ""
    for match in matches:
        lost_item_id, user_id = match[0], match[3]
        cursor.execute("UPDATE Found_Items SET status='matched' WHERE found_item_id=%s", (found_item_id,))
        cursor.execute("UPDATE Lost_Items SET status='matched' WHERE lost_item_id=%s", (lost_item_id,))
        conn.commit()
        match_info += f"Match Found! Lost Item ID: {lost_item_id} (Owner ID: {user_id})<br>"
    if not match_info:
        match_info = "No matches found yet."
    return render_template("message.html", message="Found Item Added.<br>" + match_info, color="alert-primary")

@app.route("/add_lost_item", methods=['post'])
def add_lost_item():
    item_name = request.form.get("item_name")
    lost_date = request.form.get("lost_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    user_id = session['user_id']
    cursor.execute("INSERT INTO Lost_Items (item_name, lost_date, location_id, description, user_id) VALUES (%s,%s,%s,%s,%s)",
                   (item_name, lost_date, location_id, description, user_id))
    conn.commit()
    lost_item_id = cursor.lastrowid
    cursor.execute("SELECT found_item_id, item_name, found_date, finder_id FROM Found_Items WHERE location_id=%s AND item_name LIKE %s AND status='Found'", (location_id, f"%{item_name}%"))
    matches = cursor.fetchall()
    match_info = ""
    for match in matches:
        found_item_id, finder_id = match[0], match[3]
        cursor.execute("UPDATE Lost_Items SET status='matched' WHERE lost_item_id=%s", (lost_item_id,))
        cursor.execute("UPDATE Found_Items SET status='matched' WHERE found_item_id=%s", (found_item_id,))
        conn.commit()
        match_info += f"Match Found! Found Item ID: {found_item_id} (Finder ID: {finder_id})<br>"
    if not match_info:
        match_info = "No matches found yet."
    return render_template("message.html", message="Lost Item Added.<br>" + match_info, color="alert-primary")

@app.route("/edit_lost_item")
def edit_lost_item():
    lost_item_id = request.args.get("lost_item_id")
    cursor.execute("select * from Lost_Items where lost_item_id=%s", (lost_item_id,))
    Lost_Item = cursor.fetchone()
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    return render_template("edit_lost_item.html", Lost_Item=Lost_Item, locations=locations, lost_item_id=lost_item_id)

@app.route("/edit_found_item")
def edit_found_item():
    found_item_id = request.args.get("found_item_id")
    cursor.execute("select * from Found_Items where found_item_id=%s", (found_item_id,))
    Found_Item = cursor.fetchone()
    cursor.execute("select * from Locations")
    locations = cursor.fetchall()
    return render_template("edit_found_item.html", Found_Item=Found_Item, locations=locations, found_item_id=found_item_id)

@app.route("/edit_lost_item_action", methods=['post'])
def edit_lost_item_action():
    lost_item_id = request.form.get("lost_item_id")
    item_name = request.form.get("item_name")
    lost_date = request.form.get("lost_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    cursor.execute("update Lost_Items set item_name=%s, lost_date=%s, location_id=%s, description=%s where lost_item_id=%s",
                   (item_name, lost_date, location_id, description, lost_item_id))
    conn.commit()
    return redirect("/lost_items")

@app.route("/edit_found_item_action", methods=['post'])
def edit_found_item_action():
    found_item_id = request.form.get("found_item_id")
    item_name = request.form.get("item_name")
    found_date = request.form.get("found_date")
    location_id = request.form.get("location_id")
    description = request.form.get("description")
    cursor.execute("update Found_Items set item_name=%s, found_date=%s, location_id=%s, description=%s where found_item_id=%s",
                   (item_name, found_date, location_id, description, found_item_id))
    conn.commit()
    return redirect("/found_items")

@app.route("/delete_lost_item")
def delete_lost_item():
    lost_item_id = request.args.get("lost_item_id")
    cursor.execute("delete from Lost_Items where lost_item_id=%s", (lost_item_id,))
    conn.commit()
    return redirect("/lost_items")

@app.route("/delete_found_item")
def delete_found_item():
    found_item_id = request.args.get("found_item_id")
    cursor.execute("delete from Found_Items where found_item_id=%s", (found_item_id,))
    conn.commit()
    return redirect("/found_items")

@app.route("/claim_lost_item")
def claim_lost_item():
    lost_item_id = request.args.get("lost_item_id")
    return render_template("claim_lost_item.html", lost_item_id=lost_item_id)

@app.route("/claim_lost_item2")
def claim_lost_item2():
    user_id = session['user_id']
    lost_item_id = request.args.get("lost_item_id")
    claim_message = request.args.get("claim_message")
    cursor.execute("SELECT * FROM Claims WHERE user_id=%s AND lost_item_id=%s AND claim_status='Pending'", (user_id, lost_item_id))
    if cursor.fetchone():
        return render_template("message.html", message="You have already claimed this item.", color="alert-danger")
    cursor.execute("SELECT found_item_id FROM Found_Items WHERE item_name IN (SELECT item_name FROM Lost_Items WHERE lost_item_id=%s) AND status='Matched' LIMIT 1", (lost_item_id,))
    found_item = cursor.fetchone()
    if not found_item:
        return render_template("message.html", message="No matching found item available.", color="alert-warning")
    found_item_id = found_item[0]
    cursor.execute("INSERT INTO Claims (user_id, lost_item_id, found_item_id, claim_status, claim_message) VALUES (%s,%s,%s,'Pending',%s)",
                   (user_id, lost_item_id, found_item_id, claim_message))
    cursor.execute("UPDATE Lost_Items SET status='Claimed' WHERE lost_item_id=%s", (lost_item_id,))
    cursor.execute("UPDATE Found_Items SET status='Claimed' WHERE found_item_id=%s", (found_item_id,))
    conn.commit()
    return render_template("message.html", message="Claim submitted successfully!", color="alert-success")

@app.route("/claim_found_item")
def claim_found_item():
    found_item_id = request.args.get("found_item_id")
    return render_template("claim_found_item.html", found_item_id=found_item_id)

@app.route("/claim_found_item2")
def claim_found_item2():
    if 'user_id' not in session:
        return redirect("/userLogin")
    user_id = session['user_id']
    found_item_id = request.args.get("found_item_id")
    claim_message = request.args.get("claim_message")
    cursor.execute("SELECT * FROM Claims WHERE user_id=%s AND found_item_id=%s AND claim_status='Pending'", (user_id, found_item_id))
    if cursor.fetchone():
        return render_template("message.html", message="You have already claimed this item.", color="alert-danger")
    cursor.execute("SELECT lost_item_id FROM Lost_Items WHERE item_name IN (SELECT item_name FROM Found_Items WHERE found_item_id=%s) AND status='Matched' LIMIT 1", (found_item_id,))
    lost_item = cursor.fetchone()
    if not lost_item:
        return render_template("message.html", message="No matching lost item available.", color="alert-warning")
    lost_item_id = lost_item[0]
    cursor.execute("INSERT INTO Claims (user_id, lost_item_id, found_item_id, claim_status, claim_message) VALUES (%s,%s,%s,'Pending',%s)",
                   (user_id, lost_item_id, found_item_id, claim_message))
    cursor.execute("UPDATE Lost_Items SET status='Claimed' WHERE lost_item_id=%s", (lost_item_id,))
    cursor.execute("UPDATE Found_Items SET status='Claimed' WHERE found_item_id=%s", (found_item_id,))
    conn.commit()
    return render_template("message.html", message="Claim submitted successfully!", color="alert-success")

@app.route("/claimed_items")
def claimed_items():
    cursor.execute("""
        SELECT c.claim_id, c.claim_status, c.verification_date, c.claim_message,
               u.name AS user_name, u.email AS user_email,
               l.item_name AS lost_item_name, l.lost_date, loc_l.location_name AS lost_location,
               f.item_name AS found_item_name, f.found_date, loc_f.location_name AS found_location
        FROM Claims c
        LEFT JOIN Users u ON c.user_id = u.user_id
        LEFT JOIN Lost_Items l ON c.lost_item_id = l.lost_item_id
        LEFT JOIN Locations loc_l ON l.location_id = loc_l.location_id
        LEFT JOIN Found_Items f ON c.found_item_id = f.found_item_id
        LEFT JOIN Locations loc_f ON f.location_id = loc_f.location_id
        ORDER BY c.claim_id DESC
    """)
    claims = cursor.fetchall()
    return render_template("claimed_items.html", claims=claims)

@app.route("/approve_claim")
def approve_claim():
    if 'role' not in session or session['role'] != 'admin':
        return redirect("/adminLogin")
    claim_id = request.args.get("claim_id")
    cursor.execute("SELECT lost_item_id, found_item_id FROM Claims WHERE claim_id=%s", (claim_id,))
    result = cursor.fetchone()
    if result:
        lost_item_id, found_item_id = result
        cursor.execute("UPDATE Claims SET claim_status='Approved', verification_date=NOW() WHERE claim_id=%s", (claim_id,))
        cursor.execute("UPDATE Lost_Items SET status='Returned' WHERE lost_item_id=%s", (lost_item_id,))
        cursor.execute("UPDATE Found_Items SET status='Returned' WHERE found_item_id=%s", (found_item_id,))
        conn.commit()
    return redirect("/claimed_items")

@app.route("/reject_claim")
def reject_claim():
    if 'role' not in session or session['role'] != 'admin':
        return redirect("/adminLogin")
    claim_id = request.args.get("claim_id")
    cursor.execute("SELECT lost_item_id, found_item_id FROM Claims WHERE claim_id=%s", (claim_id,))
    result = cursor.fetchone()
    if result:
        lost_item_id, found_item_id = result
        cursor.execute("UPDATE Claims SET claim_status='Rejected', verification_date=NOW() WHERE claim_id=%s", (claim_id,))
        cursor.execute("UPDATE Lost_Items SET status='Matched' WHERE lost_item_id=%s", (lost_item_id,))
        cursor.execute("UPDATE Found_Items SET status='Matched' WHERE found_item_id=%s", (found_item_id,))
        conn.commit()
    return redirect("/claimed_items")

app.run(debug=True)
