import pymysql
from flask import Flask, render_template, request,session,redirect

app = Flask(__name__)
app.secret_key="lostandfound"

conn = pymysql.connect(host="localhost",db="lost_and_found",user="root",password="root")
cursor = conn.cursor()


app.run(debug=True)