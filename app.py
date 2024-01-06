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
        #The format of user name [doc-0
        # 00,patient-000,admin-000] 
        #doc for doctors ,patient for patient ,admin for admins
        if user_name and password:
            prefix=user_name.split('-')[0]
            if prefix == 'doc':
                account_type='doctors'
                session['user_type'] ='doctor'
            elif prefix == 'patient':
                account_type='patients'
                session['user_type'] ='patient'
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
                if account_type == 'doctors':
                    return redirect('/doctor_profile')
                elif account_type == 'patients':
                    return redirect('/patient_profile')
                else:
                    return redirect('/admin_page')
            else:
                message = 'Invalid user name or password'

    return render_template('sign_in.html', msg=message)


@app.route('/add_doctor', methods=['POST','GET'])
def add_doctor():
    message = ''
    print(session.get('logged_in') , session.get('user_type'))
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
                message="You have successfully add doctor with username: "+username+"  password: "+password
    return render_template('add_doctor.html',msg=message)


@app.route('/flash_messages')
def flash_messages():
    messages = get_flashed_messages()
    return render_template('flash_messages.html', messages=messages)


@app.route('/new_patient',methods=['GET', 'POST'])
def new_patient():
    message = ''
    if request.method == 'POST':
        # get the data from the form
        first_name = request.form.get("first-name")
        last_name = request.form.get("last-name")
        gender = request.form.get("gender")
        city = request.form.get("city")
        street = request.form.get("street")
        # Extract birth date from the form
        birth_date_str = request.form.get('birth_date')
        # Convert the string to a datetime.date object
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        phone_number=request.form.get("phone-number")
        password=request.form.get("password")
        if phone_number:
            cursor.execute('SELECT PhoneNumber FROM Patients WHERE PhoneNumber = %s', (phone_number,))
            if cursor.fetchone():
                message = 'The phone number is linked to another account'
            else:
                cursor.execute(
                    'INSERT INTO Patients(FirstName, LastName, Gender , City  ,Street ,DateOfBirth,PhoneNumber  ) VALUES (%s, %s, %s , %s  ,%s ,%s,%s  )',
                    (first_name, last_name, gender, city, street,birth_date,phone_number))
                database_hospital.commit()
                cursor.execute('SELECT PatientID FROM Patients WHERE PhoneNumber=%s',(phone_number,))
                PatientID = str(dict(cursor.fetchone())['patientid'])
                if 'profile_image' in request.files:
                    f = request.files['profile_image']
                    if f.filename:
                        file_data = f.filename.split(".")
                        filename = PatientID + "." + file_data[1]
                        file_path = os.path.join(app.config['UPLOAD_PATIENT_IMG'], filename)
                        f.save(os.path.join(app.config['UPLOAD_PATIENT_IMG'], filename))
                        cursor.execute('UPDATE Patients  SET PatientImage = %s WHERE PatientID= %s', (file_path, PatientID))
                        database_hospital.commit()
                username="patient-"+PatientID
                cursor.execute('INSERT INTO Patients_accounts (PatientID,UserName,Password) values(%s,%s,%s)',
                                (PatientID,username,password))
                database_hospital.commit()
                message="You have successfully create account  your username:"+username

    return render_template("new_patient.html",msg=message)



@app.route('/patient_profile')
def patient_profile():
    if  session.get('logged_in') and session.get('user_type') == 'patient':
        
        patient_id=session['user_account']['patientid']
        cursor.execute(''' SELECT *
                    FROM Patients 
                    WHERE PatientID=%s;''' ,(patient_id,))
        info = cursor.fetchone()
        if info:
            session['patient_info'] = dict(info)
    return render_template('patient.html')

@app.route('/doctor_profile')
def doctor_profile():
    if  session.get('logged_in') and session.get('user_type') == 'doctor':
        
        doctor_id=session['user_account']['doctorid']
        cursor.execute(''' SELECT *
                    FROM Doctors 
                    WHERE DoctorID=%s;''' ,(doctor_id,))
        info = cursor.fetchone()
        if info:
            session['doctor_info'] = dict(info)
    return render_template('doctor.html')


@app.route('/admin_page')
def admin_page():
    return render_template('admin.html')



@app.route('/find_doctor', methods=['POST', 'GET'])
def find_doctor():
    if request.method == 'POST':
        department_name = request.form.get('department_name')
        doctor_name = request.form.get('doctor_name')
        first_name = ''
        last_name = ''

        if doctor_name:
            name_parts = doctor_name.split()
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Use parameterized query to prevent SQL injection
        cursor.execute('''
            SELECT *
            FROM Doctors
            INNER JOIN Departments ON Doctors.departmentid = Departments.departmentid
            WHERE DepartmentName LIKE %s AND ((FirstName LIKE %s AND LastName LIKE %s) OR %s)
        ''', (f'%{department_name}%', f'%{first_name}%', f'%{last_name}%', doctor_name == ""))

        doctors = cursor.fetchall()
        # Render a template and pass the data to be displayed in the HTML
        return render_template("find_doctor.html", doctors=doctors)

    # If the request method is not POST, render the search form
    return render_template("find_doctor.html")






@app.route('/book_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def book_doctor(doctor_id):
    msg=''
    if request.method == 'POST':
        appointment_date = request.form['appointment_date']
        start_hour = request.form['start_hour']
        end_hour = request.form['end_hour']
        purpose = request.form['purpose']
        patient_id = request.form['patient_id']

        # Check doctor's availability
        if is_doctor_available(doctor_id, appointment_date, start_hour, end_hour):
            # Insert new appointment
            insert_appointment(appointment_date, start_hour, end_hour, purpose, patient_id, doctor_id)
            return render_template('book_appointment.html',message='You book successfully')
        else:
            return render_template('book_appointment.html',message='Doctor is not available during the specified time.')
    # Render the form to book an appointment
    return render_template('book_appointment.html', doctor_id=doctor_id)

def is_doctor_available(doctor_id, appointment_date, start_hour, end_hour):
    # Check if there are any overlapping appointments for the selected doctor during the specified time range
    cursor.execute('''
        SELECT *
        FROM Appointments
        WHERE DoctorID = %s
          AND AppointmentDate = %s
          AND NOT (end_hour <= %s OR start_hour >= %s)
    ''', (doctor_id, appointment_date, start_hour, end_hour))
    overlapping_appointments = cursor.fetchall()
    return not overlapping_appointments

def insert_appointment(appointment_date, start_hour, end_hour, purpose, patient_id, doctor_id):
    # Insert a new appointment record into the Appointments table
    cursor.execute('''
        INSERT INTO Appointments (AppointmentDate, start_hour, end_hour, Purpose, PatientID, DoctorID)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (appointment_date, start_hour, end_hour, purpose, patient_id, doctor_id))
    database_hospital.commit()


@app.route('/my_calendar/<int:doctor_id>')
def my_calendar(doctor_id):
    cursor.execute('SELECT * FROM Appointments WHERE DoctorID =%s ',(doctor_id,))
    meetings = cursor.fetchall()
    event_data = [{'title': f"Appointments with Patient {meeting['patientid']}",
                   'start': f"{meeting['appointmentdate']}T{meeting['start_hour']}",
                   'end': f"{meeting['appointmentdate']}T{meeting['end_hour']}"}
                  for meeting in meetings]
    return render_template('calendar.html', events=event_data)




@app.route('/my_patients/<int:doctor_id>')
def my_patients(doctor_id):
    cursor.execute('''SELECT *
                   FROM Appointments INNER JOIN Patients  ON Appointments.patientid = Patients.patientid WHERE DoctorID =%s ''',(doctor_id,))
    patients_appointments= cursor.fetchall()
    patients = [{'id': f"{patient_appointment['patientid']}",
                'name': f"{patient_appointment['firstname']}  {patient_appointment['lastname']}",
                'image' : f"{patient_appointment['patientimage']}"}
                  for patient_appointment in patients_appointments]
    return render_template('my_patients.html',patients=patients)



@app.route('/show_history/<int:patient_id>')
def show_history(patient_id):
    cursor.execute('''SELECT *
                   FROM medical_history WHERE PatientID =%s ''', (patient_id,))
    history = cursor.fetchall()
    if not history:
        return render_template('show_history.html', msg="No Medical History Found!")
    else:
        patients_history = [{'PatientID': f"{p_history['patientid']}",
                             'Disease': f"{p_history['disease']}",
                             'description': f"{p_history['description']}"}
                            for p_history in history]
        return render_template("show_history.html", patients_history=patients_history)




@app.route('/add_to_history' ,methods=['GET', 'POST'])
def addToHistory ():
    msg=''
    if request.method=='POST':
        patient_id = request.form['patient_id']
        disease = request.form['disease']
        description = request.form['description']
        cursor.execute('''
                        SELECT PatientID 
                        FROM Patients
                        WHERE PatientID= %s
                        ''',(patient_id,))
        if cursor.fetchone:
            cursor.execute('INSERT INTO medical_history (PatientID,Disease,description) values(%s,%s,%s)',
                                (patient_id,disease,description))
            database_hospital.commit()
            msg='Added successfully'
    return render_template("add_to_history.html",msg=msg)

@app.route('/add_to_history/<int:patient_id>', methods=['GET', 'POST'])
def add_to_history(patient_id):
    if request.method == 'GET':
        return render_template("add_to_history.html", patient_id=patient_id)
    # Rest of your route implementation

    
@app.route('/add_prescription/<int:patient_id>')
def add_prescription (patient_id):
    return render_template("add_prescription.html",patient_id=patient_id)



@app.route('/add_prescription' ,methods=['GET', 'POST'])
def addPrescription ():
    msg=''
    if request.method=='POST':
        patient_id = request.form['patient_id']
        disease = request.form['disease']
        medicine=request.form['medicine']
        description = request.form['description']
        cursor.execute('''
                        SELECT PatientID 
                        FROM Patients
                        WHERE PatientID= %s
                        ''',(patient_id,))
        if cursor.fetchone:
            cursor.execute('INSERT INTO prescription (PatientID,Disease,description,Medicine) values(%s,%s,%s,%s)',
                                (patient_id,disease,description,medicine))
            database_hospital.commit()
            msg='Added successfully'
    return render_template("add_prescription.html",msg=msg)




@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    msg=''
    if request.method == 'POST':
        sender_email = request.form['email']
        description = request.form['message']

        # Insert the form data into the 'messages' table
        cursor.execute('INSERT INTO messages (sender_email, description) VALUES (%s, %s)',
                       (sender_email, description))

        # Commit the changes to the database
        database_hospital.commit()

    # Render the contact us form template for GET requests
    return render_template('contact_us.html',msg=msg)



@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    
    # Redirect to the home page or any other desired location
    return redirect('/')




@app.route('/my_appointments/<int:patient_id>')
def my_appointments(patient_id):
    cursor.execute('''SELECT *
                   FROM Appointments WHERE PatientID = %s ''', (patient_id,))
    appointments = cursor.fetchall()
    if not appointments:
        return render_template('my_appointments.html', msg="No appointments found!")
    else:
        patients_appointments = [{'AppointmentDate': f"{appointment['appointmentdate']}",
                                  'start_hour': f"{appointment['start_hour']}",
                                  'end_hour': f"{appointment['end_hour']}",
                                  'Purpose': f"{appointment['purpose']}",
                                  'DoctorID': f"{appointment['doctorid']}"
                                  }
                                 for appointment in appointments]
        return render_template("my_appointments.html", patients_appointments=patients_appointments)

    


@app.route('/my_prescriptions/<int:patient_id>')
def my_prescriptions(patient_id):
    cursor.execute('''SELECT *
                   FROM prescription WHERE PatientID = %s ''', (patient_id,))
    prescriptions = cursor.fetchall()
    if not prescriptions:
        return render_template('my_prescriptions.html', msg="No prescriptions Found!")
    else:
        patients_prescriptions = [{'Disease': f"{p_prescription['disease']}",
                                   'Medicine': f"{p_prescription['medicine']}",
                                   'description': f"{p_prescription['description']}"
                                   }
                                  for p_prescription in prescriptions]
        return render_template("my_prescriptions.html", patients_prescriptions=patients_prescriptions)
