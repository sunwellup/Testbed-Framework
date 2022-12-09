from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'ntu-testbed.cidlvgyuihjt.ap-southeast-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'ntutestbed2022'
app.config['MYSQL_DB'] = 'testbed'

# Intialize MySQL
mysql = MySQL(app)
_host = 'ntu-testbed.cidlvgyuihjt.ap-southeast-1.rds.amazonaws.com';
_user = 'admin';
_password = 'ntutestbed2022';
_DBname = 'testbed';

@app.route('/Login', methods=['GET', 'POST'])
def login():

    # Output message if something goes wrong...
    msg = ''

    if request.method == 'POST':
        # Create variables for easy access
        username = request.form['uname']
        password = request.form['psw']

        mydb = mysql.connect(host=_host, user=_user, password=_password, database=_DBname)
        mycursor = mydb.cursor()
        sql = "INSERT INTO login (username, password) VALUES (%s, %s)"
        val = (username, password)
        mycursor.execute(sql, val)
        mydb.commit()
        print(mycursor.rowcount, "record inserted.")
        # Fetch one record and return result
        account = mycursor.fetchone()
            # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return 'Logged in successfully!'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html')

    
if __name__ == "__main__":
    app.run(debug=True)