import os
import pyodbc
import hashlib
from functools import wraps
from flask import Flask, session, request, render_template, redirect, url_for

# START-STUDENT-CODE
# Define the DSN for the ODBC connection to your PostgreSQL database.
DSN = "DRIVER=PostgreSQL;SERVER=faure.cs.colostate.edu;PORT=5432;DATABASE=tyseef;UID=tyseef;PWD=836274587"
# END-STUDENT-CODE

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    return hash_password(password) == hashed


def parse_float(value):
    return float(value) if value.replace('.', '', 1).isdigit() else None


def parse_int(value):
    return int(value) if value.isdigit() else None


def get_employees():
    # START-STUDENT-CODE
    # 1. Connect to the database using pyodbc and DSN.
    # 2. Retrieve employees with their roles (Manager, Technician, ATC) or blank.
    # 3. Close the connection and return the result.

    employees = []
    
    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()
    cursor.execute('''
                   SELECT e.ssn, e.name, e.address, e.phone, e.salary,
                   CASE
                        WHEN m.ssn IS NOT NULL THEN 'Manager'
                        WHEN t.ssn IS NOT NULL THEN 'Technician'
                        WHEN a.ssn IS NOT NULL THEN 'ATC'
                        ELSE ''
                    END AS role
                    FROM airport.employee e
                    LEFT JOIN airport.manager m ON e.ssn = m.ssn
                    LEFT JOIN airport.technician t ON e.ssn = t.ssn
                    LEFT JOIN airport.atc a ON e.ssn = a.ssn;
                   ''')
    employees = cursor.fetchall()
    cnxn.close()

    # END-STUDENT-CODE
    return employees


def get_airplane_models():
    # START-STUDENT-CODE
    # 1. Connect to the database
    # 2. Retrieve all airplane models (model_number, capacity, weight)
    # 3. Close the connection

    models = []
    
    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM airport.airplane_model")
    models = cursor.fetchall()
    cnxn.close()

    # END-STUDENT-CODE
    return models


def get_airplanes():
    # START-STUDENT-CODE
    # 1. Connect to the database
    # 2. Retrieve all airplanes (reg_number, model_number)
    # 3. Close the connection

    airplanes = []
    
    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM airport.airplane")
    airplanes = cursor.fetchall()
    cnxn.close()

    # END-STUDENT-CODE
    return airplanes


def get_faa_tests():
    # START-STUDENT-CODE
    # 1. Connect to the database
    # 2. Retrieve all FAA tests (test_number, name, max_score)
    # 3. Close the connection

    faa_tests = []
    
    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM airport.faa_test")
    faa_tests = cursor.fetchall()
    cnxn.close()

    # END-STUDENT-CODE
    return faa_tests


def get_airworthiness_tests():
    # START-STUDENT-CODE
    # 1. Connect to the database
    # 2. Retrieve all airworthiness test events (test_number, ssn, reg_number, date, duration, score)
    # 3. Close the connection

    tests = []
    
    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM airport.test_event") # Need to verify
    tests = cursor.fetchall()
    cnxn.close()

    # END-STUDENT-CODE
    return tests


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # START-SAMPLE-SOLUTION
        # 1. Connect to the DB
        # 2. Select manager based on SSN and retrieve the password
        # 3. Close the connection
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()
        cursor.execute('''
            SELECT e.password
            FROM airport.employee e
            JOIN airport.manager m ON e.ssn = m.ssn
            WHERE e.ssn = ?
        ''', (username,))
        user = cursor.fetchone()
        cnxn.close()
        # END-SAMPLE-SOLUTION

        if user and verify_password(password, user[0]):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message="Authentication error!")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
def employee_add():
    employees = get_employees()

    if request.method == 'POST':
        ssn = request.form['ssn'].strip()
        name = request.form['name'].strip() or None
        password = request.form['password'].strip() or None
        address = request.form['address'].strip() or None
        phone = request.form['phone'].strip() or None
        salary = request.form['salary'].strip()
        specialization = request.form.get('specialization')

        salary = parse_float(salary)
        password_hashed = hash_password(password) if password else None

        # START-STUDENT-CODE
        # 1. Connect to DB
        # 2. Check if this SSN already exists
        # 3. If not, insert into employee and handle specialization
        # 4. Close connection
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()
        try:
            cursor.execute('''
                INSERT INTO airport.employee (ssn, name, password, address, phone, salary)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (ssn) DO NOTHING;
            ''', (ssn, name, password_hashed, address, phone, salary))

            if specialization == 'manager':
                cursor.execute('''
                    INSERT INTO airport.manager (ssn)
                    VALUES (?)
                    ON CONFLICT DO NOTHING;
                ''', (ssn,))
            elif specialization == 'technician':
                cursor.execute('''
                    INSERT INTO airport.technician (ssn)
                    VALUES (?)
                    ON CONFLICT DO NOTHING;
                ''', (ssn,))
            elif specialization == 'atc':
                cursor.execute('''
                    INSERT INTO airport.atc (ssn)
                    VALUES (?)
                    ON CONFLICT DO NOTHING;
                ''', (ssn,))
            cnxn.commit()
        except Exception as e:
            cnxn.rollback()
            return render_template('employees.html', message="Transaction failed: " + e)

        cnxn.close()
        # END-STUDENT-CODE

        return redirect(url_for('employee_add'))

    return render_template('employees.html', employees=employees, action='Add')


@app.route('/employee/update', methods=['GET', 'POST'])
@login_required
def employee_update():
    employees = get_employees()

    if request.method == 'POST':
        ssn = request.form['ssn'].strip()
        name = request.form['name'].strip() or None
        password = request.form['password'].strip() or None
        address = request.form['address'].strip() or None
        phone = request.form['phone'].strip() or None
        salary = request.form['salary'].strip()
        specialization = request.form.get('specialization')

        salary = parse_float(salary)
        password_hashed = hash_password(password) if password else None

        # START-STUDENT-CODE
        # 1. Connect to DB
        # 2. Check if employee with SSN exists
        # 3. If exists, update non-empty fields
        # 4. Handle specialization
        # 5. Close connection

        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()
        
        fields = []
        values = []
        
        if name:
            fields.append('name = ?')
            values.append(name)

        if password_hashed:
            fields.append('password = ?')
            values.append(password_hashed)

        if address:
            fields.append('address = ?')
            values.append(address)

        if phone:
            fields.append('phone = ?')
            values.append(phone)

        if salary is not None:
            fields.append('salary = ?')
            values.append(salary)

        if specialization:
            cursor.execute('DELETE FROM airport.manager WHERE ssn = ?', (ssn,))
            cursor.execute('DELETE FROM airport.technician WHERE ssn = ?', (ssn,))
            cursor.execute('DELETE FROM airport.atc WHERE ssn = ?', (ssn,))

            if specialization == 'manager':
                cursor.execute('''
                    INSERT INTO airport.manager (ssn)
                    VALUES (?)
                ''', (ssn,))
            elif specialization == 'technician':
                cursor.execute('''
                    INSERT INTO airport.technician (ssn)
                    VALUES (?)
                ''', (ssn,))
            elif specialization == 'atc':
                cursor.execute('''
                    INSERT INTO airport.atc (ssn)
                    VALUES (?)
                ''', (ssn,))

        if fields: 

            query = f'''
                    UPDATE airport.employee
                    SET {', '.join(fields)}
                    WHERE ssn = ?;
            '''
            values.append(ssn)

            cursor.execute(query, values)
        
        cnxn.commit()
        cnxn.close()

        # END-STUDENT-CODE

        return redirect(url_for('employee_update'))

    return render_template('employees.html', employees=employees, action='Update')


@app.route('/employee/delete', methods=['GET', 'POST'])
@login_required
def employee_delete():
    employees = get_employees()

    if request.method == 'POST':
        ssn = request.form['ssn'].strip()

        # START-STUDENT-CODE
        # 1. Connect to DB
        # 2. Delete the employee's specializations
        # 3. Delete from employee
        # 4. Close connection

        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        cursor.execute('DELETE FROM airport.manager WHERE ssn = ?', (ssn,))
        cursor.execute('DELETE FROM airport.technician WHERE ssn = ?', (ssn,))
        cursor.execute('DELETE FROM airport.atc WHERE ssn = ?', (ssn,))
        cursor.execute('DELETE FROM airport.expert WHERE ssn = ?', (ssn,))
        cursor.execute('DELETE FROM airport.employee WHERE ssn = ?', (ssn,))


        cnxn.commit()
        cnxn.close()
        # END-STUDENT-CODE

        return redirect(url_for('employee_delete'))

    return render_template('employees.html', employees=employees, action='Delete')


@app.route('/expertise', methods=['GET', 'POST'])
@login_required
def expertise():
    # START-STUDENT-CODE
    # 1. Connect to DB
    # 2. If POST, add or remove expertise from 'expert' table
    # 3. Retrieve technicians + models for dropdowns
    # 4. Close connection

    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()

    if request.method == 'POST':
        ssn = request.form['ssn'].strip()
        model_number = request.form['model_number'].strip()
        action = request.form['action']

        values = [ssn, model_number]

        if action == "add":
            query = '''
                    INSERT INTO airport.expert (ssn, model_number)
                    VALUES (?, ?)
                    ON CONFLICT DO NOTHING;
            '''
        elif action == "remove":
            query = '''
                    DELETE FROM airport.expert
                    WHERE ssn = ? AND model_number = ?;
            '''

        cursor.execute(query, values)

    cursor.execute('''
        SELECT e.ssn, e.name, COALESCE(ex.model_number, '')
        FROM airport.employee e
        INNER JOIN airport.technician t ON e.ssn = t.ssn
        LEFT JOIN airport.expert ex ON e.ssn = ex.ssn
        ORDER BY e.name, ex.model_number;
    ''')

    technicians = cursor.fetchall()

    formatted_technicians = [
        (tech[0], tech[1], tech[2] if tech[2] is not None else '') for tech in technicians
    ]

    models = []

    cursor.execute('''
        SELECT model_number FROM airport.airplane_model
        ORDER BY model_number;
    ''')

    models = cursor.fetchall()

    cnxn.commit()
    cnxn.close()
    # END-STUDENT-CODE

    return render_template('expertise.html', technicians=formatted_technicians, models=models)


@app.route('/update_salaries', methods=['GET', 'POST'])
@login_required
def update_salaries():
    if request.method == 'POST':
        percentage = parse_float(request.form['percentage'].strip())
        if percentage is not None:
            percentage = round(percentage, 2) / 100

            # START-STUDENT-CODE
            # 1. Connect to DB
            # 2. Increase salary by 'percentage' for all employees
            # 3. Close connection
            
            percentage += 1

            cnxn = pyodbc.connect(DSN)
            cursor = cnxn.cursor()

            cursor.execute('''
                UPDATE airport.employee
                SET salary = salary * ?
            ''',(percentage,))

            cnxn.commit()
            cnxn.close()

            # END-STUDENT-CODE

        return redirect(url_for('index'))

    return render_template('salary.html')


@app.route('/models/add', methods=['GET', 'POST'])
@login_required
def model_add():
    if request.method == 'POST':
        model_number = request.form['model_number'].strip()
        capacity = parse_int(request.form['capacity'].strip())
        weight = parse_float(request.form['weight'].strip())

        # START-STUDENT-CODE
        # 1. Connect to DB
        # 2. Insert new airplane model if it does not exist
        # 3. Close connection
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        cursor.execute('''
            INSERT INTO airport.airplane_model (model_number, capacity, weight)
            VALUES (?, ?, ?)
            ON CONFLICT (model_number) DO NOTHING;
        ''', (model_number, capacity, weight))

        cnxn.commit()
        cnxn.close()

        # END-STUDENT-CODE

    return render_template('models.html', models=get_airplane_models(), action="Add")


@app.route('/models/update', methods=['GET', 'POST'])
@login_required
def model_update():
    if request.method == 'POST':
        model_number = request.form['model_number'].strip()
        capacity = request.form['capacity'].strip() or None
        weight = request.form['weight'].strip() or None

        capacity = parse_int(capacity) if capacity else None
        weight = parse_float(weight) if weight else None

        # START-STUDENT-CODE
        # 1. Connect to DB
        # 2. If model exists, update non-empty fields
        # 3. Close connection

        fields = []
        values = []
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        if capacity:
            fields.append('capacity = ?')
            values.append(capacity)
        
        if weight:
            fields.append('weight = ?')
            values.append(weight)

        if fields: 

            query = f'''
                    UPDATE airport.airplane_model
                    SET {', '.join(fields)}
                    WHERE model_number = ?;
            '''
            values.append(model_number)

            cursor.execute(query, values)

        cnxn.commit()
        cnxn.close()

        # END-STUDENT-CODE

    return render_template('models.html', models=get_airplane_models(), action="Update")


@app.route('/models/delete', methods=['GET', 'POST'])
@login_required
def model_delete():
    if request.method == 'POST':
        model_number = request.form['model_number'].strip()

        # START-STUDENT-CODE
        # 1. Connect to DB
        # 2. Delete the model if it exists
        # 3. Close connection
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        cursor.execute('DELETE FROM airport.airplane WHERE model_number = ?', (model_number,))
        cursor.execute('DELETE FROM airport.expert WHERE model_number = ?', (model_number,))
        cursor.execute('DELETE FROM airport.airplane_model WHERE model_number = ?', (model_number,))

        cnxn.commit()
        cnxn.close()
        
        # END-STUDENT-CODE

    return render_template('models.html', models=get_airplane_models(), action="Delete")


@app.route('/airplanes/add', methods=['GET', 'POST'])
@login_required
def airplane_add():
    # START-STUDENT-CODE
    # 1. Connect to DB
    # 2. If POST, check if the airplane reg_number exists, otherwise insert
    # 3. Retrieve list of airplane_model for dropdown
    # 3. Close connection

    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()

    if request.method == 'POST':
        reg_number = request.form['reg_number'].strip()
        model_number = request.form['model_number'].strip()

        

        cursor.execute('''
            INSERT INTO airport.airplane (reg_number, model_number)
            VALUES (?, ?)
            ON CONFLICT (reg_number) DO NOTHING;
        ''', (reg_number, model_number))


    models = []

    cursor.execute('''
        SELECT model_number FROM airport.airplane_model
        ORDER BY model_number;
    ''')

    models = cursor.fetchall()

    cnxn.commit()
    cnxn.close()

    # END-STUDENT-CODE

    return render_template('airplanes.html', airplanes=get_airplanes(), models=models, action="Add")


@app.route('/airplanes/update', methods=['GET', 'POST'])
@login_required
def airplane_update():
    # START-STUDENT-CODE
    # 1. Connect to DB
    # 2. (POST) If airplane exists, update the model_number
    # 3. Retrieve list of airplane_model for dropdown
    # 4. Close connection

    cnxn = pyodbc.connect(DSN)
    cursor = cnxn.cursor()

    if request.method == 'POST':
        reg_number = request.form['reg_number'].strip()
        model_number = request.form['model_number'].strip()

        cursor.execute('''
            UPDATE airport.airplane
            SET model_number = ?
            WHERE reg_number = ?
        ''', (model_number, reg_number))

    models = []

    cursor.execute('''
        SELECT model_number FROM airport.airplane_model
        ORDER BY model_number;
    ''')

    models = cursor.fetchall()

    cnxn.commit()
    cnxn.close()

    # END-STUDENT-CODE

    return render_template('airplanes.html', airplanes=get_airplanes(), models=models, action="Update")


@app.route('/airplanes/delete', methods=['GET', 'POST'])
@login_required
def airplane_delete():
    # START-STUDENT-CODE
    # 1. Connect to DB
    # 2. If airplane exists, delete it
    # 3. Close connection

    if request.method == 'POST':
        reg_number = request.form['reg_number'].strip()
        model_number = request.form['model_number'].strip()
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        cursor.execute('DELETE FROM airport.test_event WHERE reg_number = ?', (reg_number,))
        cursor.execute('DELETE FROM airport.airplane WHERE reg_number = ? AND model_number = ?', (reg_number, model_number))
        
        models = []

        cursor.execute('''
            SELECT model_number FROM airport.airplane_model
            ORDER BY model_number;
        ''')

        models = cursor.fetchall()

        cnxn.commit()
        cnxn.close()

    # END-STUDENT-CODE

    return render_template('airplanes.html', airplanes=get_airplanes(), models=get_airplane_models(), action="Delete")


@app.route('/faa_tests/add', methods=['GET', 'POST'])
@login_required
def faa_test_add():
    # START-STUDENT-CODE
    # 1. Connect to DB
    # 2. If test_number doesn't exist, insert new FAA test
    # 3. Close connection

    if request.method == 'POST':
        test_number = request.form['test_number'].strip()
        name = request.form['name'].strip()
        max_score = parse_float(request.form['max_score'].strip())
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        cursor.execute('''
            INSERT INTO airport.faa_test (test_number, name, max_score)
            VALUES (?, ?, ?)
            ON CONFLICT (test_number) DO NOTHING;
        ''', (test_number, name, max_score))

        cnxn.commit()
        cnxn.close()

    # END-STUDENT-CODE

    return render_template('faa_tests.html', faa_tests=get_faa_tests(), action="Add")


@app.route('/faa_tests/update', methods=['GET', 'POST'])
@login_required
def faa_test_update():
    # START-STUDENT-CODE
    # 1. Connect to DB
    # 2. If test_number exists, update name/max_score
    # 3. Close connection

    if request.method == 'POST':
        test_number = request.form['test_number'].strip()
        name = request.form['name'].strip() or None
        max_score = request.form['max_score'].strip() or None
        max_score = parse_float(max_score) if max_score else None
        
        fields = []
        values = []
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        if name:
            fields.append('name = ?')
            values.append(name)
            
        if max_score:
            fields.append('max_score = ?')
            values.append(max_score)
            
        if fields: 

            query = f'''
                    UPDATE airport.faa_test
                    SET {', '.join(fields)}
                    WHERE test_number = ?;
            '''
            values.append(test_number)

            cursor.execute(query, values)

        cnxn.commit()
        cnxn.close()

    # END-STUDENT-CODE

    return render_template('faa_tests.html', faa_tests=get_faa_tests(), action="Update")


@app.route('/faa_tests/delete', methods=['GET', 'POST'])
@login_required
def faa_test_delete():
    # START-STUDENT-CODE
    # 1. Connect to DB
    # 2. If test_number exists, delete from faa_test
    # 3. Close connection

    if request.method == 'POST':
        test_number = request.form['test_number'].strip()
        
        cnxn = pyodbc.connect(DSN)
        cursor = cnxn.cursor()

        cursor.execute('DELETE FROM airport.test_event WHERE test_number = ?', (test_number,))
        cursor.execute('DELETE FROM airport.faa_test WHERE test_number = ?', (test_number))

        cnxn.commit()
        cnxn.close()

    # END-STUDENT-CODE

    return render_template('faa_tests.html', faa_tests=get_faa_tests(), action="Delete")


@app.route('/tests')
@login_required
def tests():
    return render_template('tests.html', tests=get_airworthiness_tests())


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
