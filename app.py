from flask import Flask, render_template, request, redirect, session,flash,get_flashed_messages
import psycopg2
import os
import psycopg2.extras

app = Flask(__name__)
app.secret_key = 'xyz2929'
database_hospital = psycopg2.connect(
    database='hospital',
    port=5432,
    host='localhost',
    user='postgres',
    password='2929'
)
cursor = database_hospital.cursor(cursor_factory=psycopg2.extras.DictCursor)



@app.route('/')
def index():
    return render_template('main.html')


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    message=''
    if request.method == 'POST':
        #Get Data from the [form]
        user_name=request.form.get("user-name")
        password=request.form.get("password")
        account_type=''
        #The format of user name [doc-000,patient-000,admin-000] 
        #doc for doctors ,patient for patient ,admin for admins
        if user_name and password:
            prefix=user_name.split('-')[0]
            if prefix == 'doc':
                account_type='doctors'
                session['user_type'] ='Doctor'
            elif prefix == 'patient':
                account_type='patients'
                session['user_type'] ='Patient'
            elif prefix == 'admin':
                account_type='admins'
                session['user_type'] ='admin'
            else:
                message = 'Username is invalid'
                return render_template('sign_in.html', msg=message)
            cursor.execute('''
                SELECT "username" 
                FROM "{}_accounts"
                WHERE "username"=%s AND "password"=%s
            '''.format(account_type), (user_name, password))

            if cursor.fetchone():
                session['logged_in'] = True
                message = 'Login successful!'
                cursor.execute('''
                           SELECT * 
                           FROM "{}_accounts"
                           WHERE UserName=%s AND Password=%s
                           '''.format(account_type), (user_name, password))
                info = cursor.fetchone()
                session['user_account'] = dict(info)
                if account_type == 'Doctors':
                    return redirect('/doctor_profile')
                elif account_type == 'Patients':
                    return redirect('/patient_profile')
                else:
                    return redirect('/admin_page')
            else:
                message = 'Invalid user name or password'

    return render_template('sign_in.html', msg=message)


@app.route('/add_doctor', methods=['POST','GET'])
def add_doctor():
    # Check if the user is logged in and is an admin
    if not session.get('logged_in') or session.get('user_type') != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect('/flash_messages')
    if request.method == 'GET':
        cursor.execute('''
                        SELECT DepartmentName,DepartmentID
                        FROM Departments
                                        ''')
        departments = cursor.fetchall()
        departments= list(departments)
        return render_template('add_doctor.html',departments=departments)
    

        

    return render_template('add_doctor.html')


@app.route('/flash_messages')
def flash_messages():
    messages = get_flashed_messages()
    return render_template('flash_messages.html', messages=messages)


  