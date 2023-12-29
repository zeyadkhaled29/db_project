from flask import Flask, render_template, request, redirect, session,flash,get_flashed_messages
import psycopg2
import os
import psycopg2.extras
from datetime import datetime
import secrets
import string



app = Flask(__name__)

upload_doctor_img = os.path.join('static', 'doctors_images')
app.config['UPLOAD_DOC_IMG'] = upload_doctor_img
upload_patient_img = os.path.join('static', 'patients_images')
app.config['UPLOAD_PATIENT_IMG'] = upload_patient_img

app.secret_key = 'xyz2929'
database_hospital = psycopg2.connect(
    database='hospital',
    port=5432,
    host='localhost',
    user='postgres',
    password='2929'
)
cursor = database_hospital.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Generate a random password
def generate_password():
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(10))  # Adjust the length as needed
    return password

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
    message = ''
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
    # If it's a POST request, then we can add a new doctor
    if request.method == 'POST':
        # Extract data from the form submission
        department_id = request.form.get('department')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        city = request.form.get('city')
        street = request.form.get('street')
        gender = request.form.get('gender')
        # Extract birth date from the form
        birth_date_str = request.form.get('birth_date')
        # Convert the string to a datetime.date object
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        if email and phone_number:
            cursor.execute('''
                        SELECT email 
                        FROM Doctors
                        WHERE email= %s AND PhoneNumber= %s 
                        ''',(email,phone_number))
            if cursor.fetchone():
                    message = 'Account already exits!'
            else:
                # Add the new doctor to the database
                cursor.execute('INSERT INTO Doctors (DepartmentID,FirstName,LastName,Email,PhoneNumber,City,Street,gender,DateOfBirth) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                            (department_id,first_name,last_name,email,phone_number,city,street,gender,birth_date))
                database_hospital.commit()

                cursor.execute('SELECT DoctorID FROM Doctors WHERE email=%s',(email,))
                DoctorID = str(dict(cursor.fetchone())['doctorid'])
                if 'profile_image' in request.files:
                    f = request.files['profile_image']
                    if f.filename:
                        file_data = f.filename.split(".")
                        filename = DoctorID + "." + file_data[1]
                        file_path = os.path.join(app.config['UPLOAD_DOC_IMG'], filename)
                        f.save(os.path.join(app.config['UPLOAD_DOC_IMG'], filename))
                        cursor.execute('UPDATE Doctors  SET DoctorImage = %s WHERE DoctorID= %s', (file_path, DoctorID))
                        database_hospital.commit()
                password=generate_password()
                username="doc-"+DoctorID
                cursor.execute('INSERT INTO Doctors_accounts (DoctorID,UserName,Password) values(%s,%s,%s)',
                                (DoctorID,username,password))
                database_hospital.commit()
                message="You have successfully added the new doctor.username:"+username+"  password: "+password
    return render_template('add_doctor.html',msg=message)


@app.route('/flash_messages')
def flash_messages():
    messages = get_flashed_messages()
    return render_template('flash_messages.html', messages=messages)


  