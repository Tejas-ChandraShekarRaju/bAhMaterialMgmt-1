from flask import Flask, render_template, redirect, request, session, flash, jsonify, url_for
from flask_mysqldb import MySQL
import hashlib
import boto3, botocore
import requests, json


from datetime import datetime
import pytz
import time
from time import mktime
import os
import time
from werkzeug.utils import secure_filename

from models.projects import projects
from constants.constants import project_fields, roles

app = Flask(__name__)
# Sql setup
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'buildahome'
app.config['MYSQL_PASSWORD'] = 'build*2019'
app.config['MYSQL_DB'] = 'buildahome2016'
app.config['UPLOAD_FOLDER'] = '../static/files'
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024
app.config['S3_SECRET'] = os.environ.get('S3_SECRET')
app.config['S3_KEY'] = os.environ.get('S3_KEY')
app.config['S3_BUCKET'] = os.environ.get('S3_BUCKET')
app.config['S3_LOCATION'] = os.environ.get('S3_LOCATION')


mysql = MySQL(app)


s3 = boto3.client(
   "s3",
   aws_access_key_id=app.config['S3_KEY'],
   aws_secret_access_key=app.config['S3_SECRET']
)

app.secret_key = 'bAhSessionKey'
ALLOWED_EXTENSIONS = ['pdf','png']


def send_to_s3(file, bucket_name, filename, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type  # Set appropriate content type as per the file
            }
        )
    except Exception as e:
        print("Something Happened: ", e)
        return e
    return 'success'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_projects():
    cur = mysql.connection.cursor()
    projects = []
    if len(session['projects']) > 0:
        if session['role'] not in ['Super Admin', 'COO', 'QS Head','Purchase Head', 'Site Engineer', 'Design Head']:
            query = 'SELECT project_id, project_name from projects WHERE is_approved=1 AND archived=0 ' \
                                      'AND project_id IN ' + str(session['projects'])
            cur.execute(query)
            projects = cur.fetchall()
        else:
            query = 'SELECT project_id, project_name from projects WHERE is_approved=1 AND archived=0'
            cur.execute(query)
            projects = cur.fetchall()
    return projects

def get_projects_for_current_user():
    if 'user_id' in session:
        user_id = session['user_id']
        role = session['role']
        cur = mysql.connection.cursor()
        if role in ['Super Admin', 'COO', 'QS Head','Purchase Head', 'Site Engineer', 'Design Head']:
            return ('All')
        elif role == 'Project Coordinator':
            query = 'SELECT project_id from project_operations_team WHERE co_ordinator='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'Project Manager':
            query = 'SELECT project_id from project_operations_team WHERE project_manager='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'Purchase Executive':
            query = 'SELECT project_id from project_operations_team WHERE purchase_executive='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'QS Engineer':
            query = 'SELECT project_id from project_operations_team WHERE qs_engineer='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'Architect':
            query = 'SELECT project_id from project_design_team WHERE architect='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'Structural Designer':
            query = 'SELECT project_id from project_design_team WHERE structural_designer='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'Electrical Designer':
            query = 'SELECT project_id from project_design_team WHERE electrical_designer='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'PHE Designer':
            query = 'SELECT project_id from project_design_team WHERE phe_designer='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        elif role == 'Senior Architect':
            query = 'SELECT project_id from project_design_team WHERE senior_architect='+str(user_id)
            cur.execute(query)
            result = cur.fetchall()
            projects = []
            for i in result:
                projects.append(i[0])
            return tuple(projects)
        else: return []

@app.route('/files/<filename>', methods=['GET'])
def files(filename):
    return redirect(app.config['S3_LOCATION']+filename)


@app.route('/', methods=['GET'])
def index():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp'
        return redirect('/erp/login')
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if 'email' in session:
            if 'last_route' in session:
                last_route = session['last_route']
                del session['last_route']
                return redirect(last_route)
            else:
                return redirect('/erp')
        else:
            return render_template('login.html')
    else:
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in list(request.form.keys()):
                flash('Missing fields. Operation failed', 'danger')
                return redirect(request.referrer)

        username = request.form['username']
        password = request.form['password']
        password = hashlib.sha256(password.encode()).hexdigest()
        cur = mysql.connection.cursor()
        query = "SELECT user_id, email, name, role, password, access_level FROM App_users WHERE email='"+username+"'"
        cur.execute(query)
        result = cur.fetchone()
        if result is not None:
            if result[4] == password:
                session['user_id'] = result[0]
                session['email'] = result[1]
                session['role'] = result[3]
                session['name'] = result[2]
                session['access_level'] = result[5]
                session['projects'] = get_projects_for_current_user()
                flash('Logged in successfully', 'success')
                return redirect('/erp')
            else:
                flash('Incorrect credentials', 'danger')
                return redirect('/erp/login')
        else:
            flash('Incorrect credentials. User not found', 'danger')
            return redirect('/erp/login')


@app.route('/mobile_app_banner', methods=['GET','POST'])
def mobile_app_banner():
    if request.method == 'GET':
        return render_template('mobile_app_banner.html')
    else:
        if 'banner' in request.files:
            file = request.files['banner']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'mobile_banner.png'))
                flash('Banner updated successfully','success')
                return redirect(request.referrer)
            else:
                flash('Invalid file type. Only png images allowed. Operation failed', 'failed')
                return redirect(request.referrer)
        else:
            flash('Missing file. Operation failed', 'failed')
            return redirect(request.referrer)


@app.route('/enter_material', methods=['GET', 'POST'])
def enter_material():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/enter_material'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'Purchase Head', 'Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        projects = get_projects()
        vendors = get_vendors()
        return render_template('enter_material.html', projects=projects, vendors=vendors)
    else:
        required_fields = ['material', 'description','vendor','project','po_no','invoice_no','invoice_date',
                           'quantity','unit','rate','gst','total_amount','difference_cost','photo_date']
        for field in required_fields:
            if field not in list(request.form.keys()):
                flash('Missing fields. Operation failed', 'danger')
                return redirect(request.referrer)

        material = request.form['material']
        description = request.form['description']
        vendor = request.form['vendor']
        project = request.form['project']
        po_no = request.form['po_no']
        invoice_no = request.form['invoice_no']
        invoice_date = request.form['invoice_date']
        quantity = request.form['quantity']
        unit = request.form['unit']
        rate = request.form['rate']
        gst = request.form['gst']
        total_amount = request.form['total_amount']
        difference_cost = request.form['difference_cost']
        photo_date = request.form['photo_date']
        cur = mysql.connection.cursor()

        material_quantity_query = 'SELECT total_quantity from kyp_material WHERE project_id='+str(project)+' AND material="'+str(material)+'"'
        cur.execute(material_quantity_query)
        result = cur.fetchone()
        if result is None:
            flash('Total quantity of material has not been specified under KYP material. Entry not recorded', 'danger')
            return redirect('/erp/enter_material')
        if float(result[0]) < (float(quantity)):
            flash('Total quantity of material exceeded limit specified under KYP material. Entry not recorded', 'danger')
            return redirect('/erp/enter_material')

        query = "INSERT into procurement (material, description, vendor, project_id, po_no, invoice_no, invoice_date," \
                "quantity, unit, rate, gst, total_amount, difference_cost, photo_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (material, description, vendor, project, po_no, invoice_no, invoice_date, quantity, unit, rate, gst, total_amount, difference_cost, photo_date)
        cur.execute(query, values)
        mysql.connection.commit()
        flash('Material was inserted successfully', 'success')
        return redirect('/erp/enter_material')


@app.route('/view_inventory', methods=['GET'])
def view_inventory():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_inventory'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'Purchase Head', 'Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    cur = mysql.connection.cursor()
    projects = get_projects()
    procurements = None
    project = None
    material = None
    material_total_quantity = None
    if 'project_id' in request.args and 'material' in request.args:
        project_id = request.args['project_id']
        material = request.args['material']
        if material == 'All':
            procurement_query = 'SELECT * from procurement WHERE project_id=' + str(
                project_id)
        else:
            procurement_query = 'SELECT * from procurement WHERE project_id='+str(project_id)+' AND material="'+str(material)+'"'
        cur.execute(procurement_query)
        procurements = cur.fetchall()
        for i in projects:
            if str(i[0]) == str(project_id):
                project = i[1]

        material_quantity_query = 'SELECT total_quantity from kyp_material WHERE project_id='+str(project_id)+' AND material="'+str(material)+'"'
        cur.execute(material_quantity_query)
        result = cur.fetchone()
        if result is not None:
            material_total_quantity = result[0]
    return render_template('view_inventory.html', projects=projects, procurements=procurements, project=project, material=material, material_total_quantity=material_total_quantity)


@app.route('/shifting_entry', methods=['GET','POST'])
def shifting_entry():
    if request.method == 'GET':
        if 'email' not in session:
            flash('You need to login to continue', 'danger')
            session['last_route'] = '/erp/view_inventory'
            return redirect('/erp/login')
        projects = get_projects()
        material_quantity_data = {
            'Cement': '',
            'Concrete': '',
            'Steel': '',
            'M Sand': '',
            'P Sand': '',
            'Aggregates': '',
            'Wall Material': '',
            'Door Window': '',
            'Flooring': '',
            'Sanitary': '',
            'Hardware': ''
        }

        return render_template('shifting_entry.html', projects=projects, material_quantity_data=material_quantity_data)
    else:
        from_project = request.form['from_project']
        to_project = request.form['to_project']
        if from_project == to_project:
            flash('Shifting entry failed. Cannot shift to same project','danger')
            return redirect(request.referrer)

        cur = mysql.connection.cursor()
        material = request.form['material']
        quantity = request.form['quantity']
        description = 'Shifting entry'

        material_quantity_query = 'SELECT total_quantity from kyp_material WHERE project_id=' + str(
            to_project) + ' AND material="' + str(material) + '"'
        cur.execute(material_quantity_query)
        result = cur.fetchone()
        if result is None:
            flash('Total quantity of material has not been specified under KYP material. Entry not recorded', 'danger')
            return redirect('/erp/enter_material')
        if float(result[0]) < (float(quantity)):
            flash('Total quantity of material exceeded limit specified under KYP material. Entry not recorded',
                  'danger')
            return redirect('/erp/enter_material')

        check_if_shifting_is_possible = 'SELECT SUM(quantity) from procurement WHERE project_id=%s AND material=%s'
        cur.execute(check_if_shifting_is_possible, (from_project, material))
        result = cur.fetchone()
        if result is None or int(result[0]) < int(quantity):
            flash('Shifting entry failed. Insufficient quantity in source project', 'danger')
            return redirect(request.referrer)
        deduction_query = "INSERT into procurement (material, description, project_id," \
                "quantity) values (%s, %s, %s, %s)"
        values = (material, description, from_project, int(quantity) * -1)
        cur.execute(deduction_query, values)

        addition_query = "INSERT into procurement (material, description, project_id," \
                          "quantity) values (%s, %s,  %s, %s)"
        values = (material, description, to_project, quantity)
        cur.execute(addition_query, values)

        mysql.connection.commit()
        flash('Shifting entry successful. Material Shifted!', 'success')
        return redirect(request.referrer)

@app.route('/create_user', methods=['GET','POST'])
def create_user():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/create_user'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Billing']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        return render_template('create_user.html', roles=roles)
    else:
        required_fields = ['name','role','email','phone','password','confirm_password']
        for field in required_fields:
            if field not in list(request.form.keys()):
                flash('Missing fields. Operation failed', 'danger')
                return redirect(request.referrer)

        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        c_password = request.form['confirm_password']
        if password != c_password:
            flash('Passwords did not match. Operation failed', 'danger')
            return redirect(request.referrer)
        cur = mysql.connection.cursor()
        password = hashlib.sha256(password.encode()).hexdigest()

        check_if_user_exists = 'SELECT user_id from App_users WHERE email="'+str(email)+'"'
        cur.execute(check_if_user_exists)
        res = cur.fetchone()
        if res is not None:
            update_query = 'UPDATE App_users set name=%s, role=%s, phone=%s, password=%s WHERE user_id='+str(res[0])
            cur.execute(update_query, (name, role, phone, password))
            flash('User with that email already exists. Role updated','warning')
        else:
            new_user_query = 'INSERT into App_users (name, role, email, phone, password) values(%s, %s, %s, %s, %s)'
            values = (name, role, email, phone, password)
            cur.execute(new_user_query, values)
            flash('User created successfully','success')
        mysql.connection.commit()
        return redirect('/erp/view_users')

@app.route('/edit_user', methods=['GET','POST'])
def edit_user():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/edit_user'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Billing']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        user_id = request.args['user_id']
        cur = mysql.connection.cursor()
        view_user_query = 'SELECT user_id, email, name, role, phone FROM App_users WHERE user_id='+str(user_id)
        cur.execute(view_user_query)
        result = cur.fetchone()
        return render_template('edit_user.html', user=result, roles=roles)
    else:
        required_fields = ['name', 'role', 'email', 'phone', 'password', 'confirm_password']
        for field in required_fields:
            if field not in list(request.form.keys()):
                flash('Missing fields. Operation failed', 'danger')
                return redirect(request.referrer)

        user_id = request.form['user_id']
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        if len(password.strip()) > 0:
            c_password = request.form['confirm_password']
            if password != c_password:
                flash('Passwords did not match. Operation failed', 'danger')
                return redirect(request.referrer)
            cur = mysql.connection.cursor()
            password = hashlib.sha256(password.encode()).hexdigest()
            values = (name, role, phone, email, password)
            update_query = 'UPDATE App_users set name=%s, role=%s, phone=%s, email=%s, password=%s WHERE user_id=' + str(user_id)
            cur.execute(update_query, values)
            flash('User details and password updated', 'success')
            mysql.connection.commit()
            return redirect('/erp/view_users')
        else:
            cur = mysql.connection.cursor()
            values = (name, role, phone, email)
            update_query = 'UPDATE App_users set name=%s, role=%s, phone=%s, email=%s WHERE user_id=' + str(user_id)
            cur.execute(update_query, values)
            flash('User updated', 'success')
            mysql.connection.commit()
            return redirect('/erp/view_users')

@app.route('/delete_user', methods=['GET'])
def delete_user():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/delete_user'
        return redirect('/erp/login')

    if session['role'] not in ['Super Admin','COO','Billing']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)

    if 'user_id' not in request.args:
        flash('Missing fields. Operation failed', 'danger')
        return redirect(request.referrer)

    user_id = request.args['user_id']
    cur = mysql.connection.cursor()
    delete_user_query = 'DELETE from App_users WHERE user_id=' + str(user_id)
    cur.execute(delete_user_query)
    mysql.connection.commit()
    flash('User deleted', 'danger')
    return redirect('/erp/view_users')


@app.route('/view_users', methods=['GET'])
def view_users():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_users'
        return redirect('/erp/login')

    if session['role'] not in ['Super Admin','COO','Billing']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)

    cur = mysql.connection.cursor()
    view_users_query = 'SELECT user_id, email, name, role, phone FROM App_users WHERE NOT role="Client"'
    cur.execute(view_users_query)
    result = cur.fetchall()
    return render_template('view_users.html', users=result)

@app.route('/contractor_registration', methods=['GET','POST'])
def contractor_registration():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/vendor_registration'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        return render_template('contractor_registration.html')
    else:
        column_names = list(request.form.keys())
        values = list(request.form.values())

        cur = mysql.connection.cursor()
        new_vendor_query = 'INSERT into contractors' + str(tuple(column_names)).replace("'", "") + 'values ' + str(
            tuple(values))
        cur.execute(new_vendor_query)
        mysql.connection.commit()
        flash ('Contractor registered', 'success')
        return redirect('/erp/view_contractors')

@app.route('/view_contractors', methods=['GET'])
def view_contractors():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_contractors'
        return redirect('/erp/login')

    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)

    cur = mysql.connection.cursor()
    contractors_query = 'SELECT id, name, code, pan, phone_number, address FROM contractors'
    cur.execute(contractors_query)
    result = cur.fetchall()
    return render_template('view_contractors.html', contractors=result)

@app.route('/edit_contractor', methods=['GET','POST'])
def edit_contractor():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/edit_contractor'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        if 'contractor_id' in request.args:
            cur = mysql.connection.cursor()
            contractor_query = 'SELECT * from contractors WHERE id=' + request.args['contractor_id']
            cur.execute(contractor_query)
            contractor_details = cur.fetchone()
            return render_template('edit_contractor.html', contractor_details=contractor_details[1:], contractor_id=request.args['contractor_id'])
    else:
        column_names = list(request.form.keys())

        update_string = ""
        for i in column_names[:-1]:
            update_string += i + '="' + request.form[i] + '", '
        # Remove the last comma
        update_string = update_string[:-2]
        update_vendor_query = 'UPDATE contractors SET ' + update_string + ' WHERE id=' + str(
            request.form['contractor_id'])
        cur = mysql.connection.cursor()
        cur.execute(update_vendor_query)
        mysql.connection.commit()
        flash('Contractor updated successfully','success')
        return redirect('/erp/view_contractors')

@app.route('/delete_contractor', methods=['GET'])
def delete_contractor():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/delete_contractor'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        if 'contractor_id' in request.args:
            cur = mysql.connection.cursor()
            contractor_query = 'DELETE from contractors WHERE id=' + request.args['contractor_id']
            cur.execute(contractor_query)
            mysql.connection.commit()
            flash('Contractor deleted', 'danger')
            return redirect('/erp/view_contractors')


@app.route('/vendor_registration', methods=['GET','POST'])
def vendor_registration():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/vendor_registration'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        return render_template('vendor_registration.html')
    else:
        column_names = list(request.form.keys())
        values = list(request.form.values())

        cur = mysql.connection.cursor()
        new_vendor_query = 'INSERT into vendors' + str(tuple(column_names)).replace("'", "") + 'values ' + str(
            tuple(values))
        cur.execute(new_vendor_query)
        mysql.connection.commit()
        flash ('Vendor registered', 'success')
        return redirect('/erp/view_vendors')

@app.route('/view_vendors', methods=['GET'])
def view_vendors():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_vendors'
        return redirect('/erp/login')

    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)

    cur = mysql.connection.cursor()
    vendors_query = 'SELECT id, name, code, contact_no FROM vendors'
    cur.execute(vendors_query)
    result = cur.fetchall()
    return render_template('view_vendors.html', vendors=result)

# Field validation for form done till here

@app.route('/view_vendor_details', methods=['GET'])
def view_vendor_details():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_vendor_details'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    vendor_details = []
    if 'vendor_id' in request.args:
        cur = mysql.connection.cursor()
        vendor_query = 'SELECT * from vendors WHERE id='+request.args['vendor_id']
        cur.execute(vendor_query)
        vendor_details = cur.fetchone()
    return render_template('view_vendor_details.html', vendor_details=vendor_details[1:])


@app.route('/edit_vendor', methods=['GET','POST'])
def edit_vendor():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/edit_vendor'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        if 'vendor_id' in request.args:
            cur = mysql.connection.cursor()
            vendor_query = 'SELECT * from vendors WHERE id=' + request.args['vendor_id']
            cur.execute(vendor_query)
            vendor_details = cur.fetchone()
            return render_template('edit_vendor.html', vendor_details=vendor_details[1:], vendor_id=request.args['vendor_id'])
    else:
        column_names = list(request.form.keys())

        update_string = ""
        for i in column_names[:-1]:
            update_string += i + '="' + request.form[i] + '", '
        # Remove the last comma
        update_string = update_string[:-2]
        update_vendor_query = 'UPDATE vendors SET ' + update_string + ' WHERE id=' + str(
            request.form['vendor_id'])
        cur = mysql.connection.cursor()
        cur.execute(update_vendor_query)
        mysql.connection.commit()
        flash('Vendor updated successfully','success')
        return redirect('/erp/view_vendor_details?vendor_id='+request.form['vendor_id'])

@app.route('/delete_vendor', methods=['GET'])
def delete_vendor():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/delete_vendor'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        if 'vendor_id' in request.args:
            cur = mysql.connection.cursor()
            vendor_query = 'DELETE from vendors WHERE id=' + request.args['vendor_id']
            cur.execute(vendor_query)
            mysql.connection.commit()
            flash('Vendor deleted', 'danger')
            return redirect('/erp/view_vendors')


def get_vendors():
    cur = mysql.connection.cursor()
    vendors_query = 'SELECT id, name, code FROM vendors'
    cur.execute(vendors_query)
    result = cur.fetchall()
    vendors = {}
    for i in result:
        vendors[str(i[0])] = str(i[1]) + str(i[2])
    return vendors

@app.route('/kyp_material', methods=['GET','POST'])
def kyp_material():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/kyp_material'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'Purchase Head', 'Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    material_quantity_data = {
        'Cement': '',
        'Concrete': '',
        'Steel': '',
        'M Sand': '',
        'P Sand': '',
        'Aggregates': '',
        'Wall Material': '',
        'Door Window': '',
        'Flooring': '',
        'Sanitary': '',
        'Hardware': ''
    }
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        projects = get_projects()

        project = None
        project_id = None
        if 'project_id' in request.args:
            project_id = request.args['project_id']
            material_query = 'SELECT * from kyp_material WHERE project_id='+str(project_id)
            cur.execute(material_query)
            result = cur.fetchall()
            for i in result:
                material_name = i[2]
                material_quantity_data[material_name] = i[3]
            for i in projects:
                if str(i[0]) == str(project_id):
                    project = i[1]
        return render_template('kyp_material.html', projects=projects, project_id=project_id, project=project, material_quantity_data=material_quantity_data)
    else:
        cur = mysql.connection.cursor()
        project_id = request.form['project_id']
        delete_old_quantity_chart_query = 'DELETE from kyp_material WHERE project_id='+str(project_id)
        cur.execute(delete_old_quantity_chart_query)
        for i in material_quantity_data:
            quantity_of_i = request.form[i]

            if len(str(quantity_of_i)):
                material_quantity_insert_query = "INSERT into kyp_material (project_id, material, total_quantity) values ("+str(project_id)+",'"+str(i)+"','"+str(quantity_of_i)+"')"

                cur.execute(material_quantity_insert_query)
                mysql.connection.commit()
        flash('Quantity chart updated successfully','success')
        return redirect('/erp/kyp_material?project_id='+str(project_id))

@app.route('/create_work_order', methods=['GET', 'POST'])
def create_work_order():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/create_work_order'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','QS Head','QS Engineer']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        projects = get_projects()
        floors = ['G + 1','G + 2','G + 3','G + 4']
        trades_query = 'SELECT DISTINCT trade from labour_stages'
        cur.execute(trades_query)
        result = cur.fetchall()
        trades = []
        for i in result:
            trades.append(i[0])
        return render_template('create_work_order.html', projects=projects, floors=floors, trades=trades)
    else:
        project_id = request.form['project']
        trade = request.form['trade']
        floors = request.form['floors']
        wo_value = request.form['wo_value']
        contractor_name = request.form['contractor_name']
        contractor_pan = request.form['contractor_pan']
        contractor_code = request.form['contractor_code']
        contractor_address = request.form['contractor_address']
        contractor_phone = request.form['contractor_phone']
        wo_number = request.form['wo_number']
        cheque_no = request.form['cheque_no']
        check_if_exist_query = 'SELECT id from work_orders WHERE project_id='+str(project_id)+' AND floors="'+str(floors)+'" AND trade="'+str(trade)+'"'
        cur = mysql.connection.cursor()
        cur.execute(check_if_exist_query)
        result = cur.fetchone()
        if result is not None:
            flash("Work order already exists. Operation failed",'danger')
            return redirect('/erp/create_work_order')
        else:
            insert_query = 'INSERT into work_orders (project_id, value, trade, floors, contractor_name, contractor_code, contractor_pan, wo_number, contractor_address, cheque_no, contractor_phone) ' \
                           'values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            values = (project_id, wo_value, trade, floors, contractor_name, contractor_code, contractor_pan, wo_number, contractor_address, cheque_no, contractor_phone)
            cur.execute(insert_query, values)
            mysql.connection.commit()
            flash('Work order created successfully', 'success')
            return redirect('/erp/create_work_order')


@app.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/create_bill'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head', 'QS Engineer']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        projects = get_projects()
        return render_template('create_bill.html',projects=projects)
    else:
        project_id = request.form['project_id']
        trade = request.form['trade']
        stage = request.form['stage']
        payment_percentage = request.form['payment_percentage']
        amount = request.form['amount']
        contractor_name = request.form['contractor_name']
        contractor_code = request.form['contractor_code']
        contractor_pan = request.form['contractor_pan']
        total_payable = float(amount)
        check_if_exists_query = 'SELECT id FROM wo_bills WHERE project_id='+str(project_id)+' AND trade="'+str(trade)+'" AND stage="'+str(stage)+'"'
        cur = mysql.connection.cursor()
        cur.execute(check_if_exists_query)
        res = cur.fetchone()
        if res is not None:
            flash("Older bill already exists. Operation failed", 'danger')
            return redirect('/erp/create_bill')
        else:
            insert_query = 'INSERT into wo_bills (project_id, trade, stage, payment_percentage, amount, total_payable, contractor_name, contractor_code, contractor_pan) values (%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s)'
            values = (project_id, trade, stage, payment_percentage, amount, total_payable, contractor_name, contractor_code, contractor_pan)
            cur.execute(insert_query, values)
            mysql.connection.commit()
            flash('Bill created successfully', 'success')
            return redirect('/erp/create_bill')

@app.route('/update_trades_for_project', methods=['POST'])
def update_trades_for_project():
    project_id = request.form['project_id']
    trades_query = 'SELECT DISTINCT trade from work_orders WHERE project_id='+str(project_id)
    cur = mysql.connection.cursor()
    cur.execute(trades_query)
    trades = []
    result = cur.fetchall()
    for i in result:
        trades.append(i[0])
    return jsonify(trades)

@app.route('/update_payment_stages', methods=['POST'])
def update_payment_stages():
    project_id = request.form['project_id']
    trade = request.form['trade']
    work_order_query = 'SELECT value, floors, contractor_name, contractor_code, contractor_pan from work_orders WHERE project_id='+str(project_id)+' AND trade="'+str(trade)+'" ORDER BY id'
    cur = mysql.connection.cursor()
    cur.execute(work_order_query)
    res = cur.fetchone()
    if res is not None:
        work_order_value = res[0]
        floors = res[1]
        contractor_name = res[2]
        contractor_code = res[3]
        contractor_pan = res[4]
        payment_stages_query = 'SELECT stage, payment_percentage from labour_stages WHERE floors="'+str(floors)+'" AND trade="'+trade+'"'
        cur.execute(payment_stages_query)
        result = cur.fetchall()
        stages = {}
        for i in result:
            stages[i[0]] = i[1].replace('%','')

        response = {'work_order_value': work_order_value, 'contractor_name': contractor_name, 'contractor_code': contractor_code, 'contractor_pan': contractor_pan, 'stages' : stages}
        return jsonify(response)

def get_bills_as_json(bills_query):
    cur = mysql.connection.cursor()
    cur.execute(bills_query)
    data = {}
    res = cur.fetchall()
    for i in res:
        project_id = i[0]
        if project_id not in data:
            data[project_id] = {'project_name': i[1], 'bills': []}
        data[project_id]['bills'].append(
            {'bill_id': i[16], 'contractor_name': i[7], 'contractor_pan': i[9], 'contractor_code': i[8], 'trade': i[17],
             'stage': i[3], 'amount': i[5], 'total_payable': i[6],
             'approval_1_amount': i[11], 'approval_1_notes': i[12], 'approval_2_amount': i[14],
             'approval_2_notes': i[15]}
        )
    return data

@app.route('/view_bills', methods=['GET'])
def view_bills():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_bills'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        bills_query = 'SELECT projects.project_id, projects.project_name, wo_bills.trade, wo_bills.stage, wo_bills.payment_percentage,' \
                         'wo_bills.amount, wo_bills.total_payable, wo_bills.contractor_name, wo_bills.contractor_code, wo_bills.contractor_pan,' \
                         'wo_bills.approval_1_status, wo_bills.approval_1_amount, wo_bills.approval_1_notes,' \
                         'wo_bills.approval_2_status, wo_bills.approval_2_amount, wo_bills.approval_2_notes, wo_bills.id, wo_bills.trade' \
                         ' FROM wo_bills INNER JOIN projects on wo_bills.project_id = projects.project_id AND ( wo_bills.approval_2_amount = 0 OR wo_bills.approval_2_amount IS NULL)'
        data = get_bills_as_json(bills_query)
        access_level = session['access_level']
        return render_template('view_bills.html', data=data, access_level=access_level)

@app.route('/delete_bill', methods=['GET'])
def delete_bill():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/delete_bill'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin','COO','Purchase Head','Purchase Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        if 'bill_id' in request.args:
            cur = mysql.connection.cursor()
            delete_bill_query = 'DELETE from wo_bills WHERE id=' + request.args['bill_id']
            cur.execute(delete_bill_query)
            mysql.connection.commit()
            flash('Bill deleted', 'danger')
            return redirect('/erp/view_bills')

@app.route('/view_approved_bills', methods=['GET'])
def view_approved_bills():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_approved_bills'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head', 'QS Engineer']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        bills_query = 'SELECT projects.project_id, projects.project_name, wo_bills.trade, wo_bills.stage, wo_bills.payment_percentage,' \
                         'wo_bills.amount, wo_bills.total_payable, wo_bills.contractor_name, wo_bills.contractor_code, wo_bills.contractor_pan,' \
                         'wo_bills.approval_1_status, wo_bills.approval_1_amount, wo_bills.approval_1_notes,' \
                         'wo_bills.approval_2_status, wo_bills.approval_2_amount, wo_bills.approval_2_notes, wo_bills.id, wo_bills.trade' \
                         ' FROM wo_bills INNER JOIN projects on wo_bills.project_id = projects.project_id AND (wo_bills.approval_2_amount != 0 AND wo_bills.approval_2_amount IS NOT NULL)'
        data = get_bills_as_json(bills_query)
        return render_template('view_approved_bills.html', data=data)

def update_work_order_balance(project_id, trade, difference_amount):
    get_wo_query = 'SELECT id, balance from work_orders WHERE project_id=' + str(
        project_id) + ' AND trade="' + trade + '"'
    cur = mysql.connection.cursor()
    cur.execute(get_wo_query)
    res = cur.fetchone()
    if res is not None:
        balance = res[1]
        if str(balance).strip() == '':
            balance = 0
        else:
            balance = float(balance)
        updated_balance = balance + float(difference_amount)
        update_wo_query = 'UPDATE work_orders SET balance='+str(updated_balance)+' WHERE id='+str(res[0])
        cur.execute(update_wo_query)
        mysql.connection.commit()

@app.route('/save_approved_bill', methods=['POST'])
def save_approved_bill():
    bill_id = request.form['bill_id']
    approved_amount = request.form['approved_amount']
    notes = request.form['notes']
    approval_level = request.form['approval_level']
    trade = request.form['trade']
    project_id = request.form['project_id']
    difference_amount = request.form['difference_amount']
    cur = mysql.connection.cursor()
    update_bill_query = ''
    if approval_level == 'Level 1':
        update_bill_query = 'UPDATE wo_bills SET approval_1_amount = "'+str(approved_amount)+'" , approval_1_notes = "'+str(notes)+'" WHERE id='+str(bill_id)
    elif approval_level == 'Level 2':
        update_bill_query = 'UPDATE wo_bills SET approval_2_amount = "'+str(approved_amount)+'" , approval_2_notes = "'+str(notes)+'" WHERE id='+str(bill_id)
    cur.execute(update_bill_query)
    if float(difference_amount) > 0 and  approval_level == 'Level 2':
        update_work_order_balance(project_id, trade, difference_amount)
    mysql.connection.commit()
    return jsonify({"message": "success"})


@app.route('/project_contractor_info', methods=["GET"])
def project_contractor_info():
    project_id = request.args['project_id']
    contractor_name = request.args['name']
    contractor_code = request.args['code']
    cur = mysql.connection.cursor()
    get_wo_query = 'SELECT w.contractor_name, w.contractor_code, w.contractor_pan, ' \
                   'w.value, w.balance, b.trade,  b.stage, b.payment_percentage, b.amount, b.approval_2_amount' \
                   ' FROM work_orders w INNER JOIN wo_bills b on ' \
                   'w.contractor_name=b.contractor_name AND w.contractor_code = b.contractor_code AND ' \
                   'w.project_id=%s AND w.contractor_name=%s AND w.contractor_code=%s AND ' \
                   'b.approval_2_amount IS NOT NULL ORDER BY w.trade'
    cur.execute(get_wo_query, (project_id, contractor_name, contractor_code))
    bills = cur.fetchall()

    get_project_query = 'SELECT project_name, project_number from projects WHERE project_id='+str(project_id)
    cur.execute(get_project_query)
    project = cur.fetchone()


    data = {'name': '', 'code': '', 'pan': '', 'value': '', 'balance': '', 'trade': ''}
    if len(bills) > 0:
        data['name'] = bills[0][0]
        data['code'] = bills[0][1]
        data['pan'] = bills[0][2]
        data['value'] = bills[0][3]
        data['balance'] = bills[0][4]
        data['trade'] = bills[0][5]

    return render_template('project_contractor_info.html', bills=bills, project=project, data=data)

def get_work_orders_for_project(project_id):
    cur = mysql.connection.cursor()
    get_wo_query = 'SELECT * from work_orders WHERE project_id='+str(project_id)+' ORDER BY trade'
    cur.execute(get_wo_query)
    res = cur.fetchall()
    return res

@app.route("/view_work_order", methods=['GET'])
def view_work_order():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_work_order'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head', 'QS Engineer']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        projects = get_projects()
        work_orders = []
        if 'project_id' in request.args:
            project_id = request.args['project_id']
            work_orders = get_work_orders_for_project(project_id)

        return render_template('view_work_orders.html', projects=projects, work_orders=work_orders)

@app.route("/view_unsigned_work_order", methods=['GET'])
def view_unsigned_work_order():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_unsigned_work_order'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head', 'QS Engineer']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        work_orders = []

        unsigned_query = 'SELECT p.project_name, p.project_number, wo.id, wo.trade, wo.value, wo.contractor_name FROM work_orders wo ' \
                         'INNER JOIN projects p on p.project_id=wo.project_id AND wo.signed=0'
        cur = mysql.connection.cursor()
        cur.execute(unsigned_query)
        result = cur.fetchall()
        for i in result:
            work_orders.append({
                'project_name': i[0],
                'project_number': i[1],
                'id': i[2],
                'trade': i[3],
                'value': i[4],
                'contractor_name': i[5],

            })

        return render_template('unsigned_work_orders.html', work_orders=work_orders)


@app.route("/view_unapproved_work_order", methods=['GET'])
def view_unapproved_work_order():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_unapproved_work_order'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        work_orders = []

        unsigned_query = 'SELECT p.project_name, p.project_number, wo.id, wo.trade, wo.value, wo.contractor_name FROM work_orders wo ' \
                         'INNER JOIN projects p on p.project_id=wo.project_id AND wo.signed=1 AND wo.approved=0'
        cur = mysql.connection.cursor()
        cur.execute(unsigned_query)
        result = cur.fetchall()
        for i in result:
            work_orders.append({
                'project_name': i[0],
                'project_number': i[1],
                'id': i[2],
                'trade': i[3],
                'value': i[4],
                'contractor_name': i[5],

            })

        return render_template('unapproved_work_order.html', work_orders=work_orders)


@app.route('/check_if_floors_updated', methods=['POST'])
def check_if_floors_updated():
    project_id = request.form['project_id']
    query = 'SELECT id, floors from work_orders WHERE project_id='+str(project_id)
    cur = mysql.connection.cursor()
    cur.execute(query)
    result = cur.fetchone()
    if result is not None:
        return jsonify({'floors_updated': True, 'floors': result[1]})
    return jsonify({'floors_updated': False})


@app.route('/view_approved_indents', methods=['GET'])
def view_approved_indents():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_approved_indents'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head', 'QS Engineer','Purchase Executive','Purchase Head']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        current_user_role = session['role']
        if current_user_role in ['Super Admin', 'COO', 'QS Head', 'QS Engineer', 'Purchase Head']:
            indents_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                            ', App_users.name, indents.timestamp FROM indents INNER JOIN projects on indents.status="approved" AND indents.project_id=projects.project_id ' \
                            ' LEFT OUTER JOIN App_users on indents.created_by_user=App_users.user_id'

            cur.execute(indents_query)
            data = []
            result = cur.fetchall()
            for i in result:
                i = list(i)
                if len(str(i[8]).strip()) > 0:
                    i[8] = str(i[8]).strip()
                    timestamp = datetime.strptime(i[8] + ' 2022 +0530', '%A %d %B %H:%M %Y %z')
                    IST = pytz.timezone('Asia/Kolkata')
                    current_time = datetime.now(IST)
                    time_since_creation = current_time - timestamp
                    difference_in_seconds = time_since_creation.total_seconds()
                    difference_in_hours = difference_in_seconds // 3600
                    if difference_in_hours >= 24:
                        difference_in_days = difference_in_hours // 24
                        hours_remaining = difference_in_hours % 24
                        i[8] = str(int(difference_in_days)) + ' days, ' + str(
                            int(hours_remaining)) + 'hours'
                    else:
                        i[8] = str(int(difference_in_hours)) + ' hours'
                data.append(i)
            return render_template('approved_indents.html', result=data)
        elif current_user_role == 'Purchase Executive':
            current_user_email = session['email']
            access_query = 'SELECT access, role from App_users WHERE email=' + str(current_user_email)
            cur.execute(access_query)
            res = cur.fetchone()
            access = res[0]
            if len(access):
                access = access.split(',')
                access_as_int = [int(i) for i in access]
                access_tuple = tuple(access_as_int)
                indents_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                                ', App_users.name, indents.timestamp FROM indents INNER JOIN projects on indents.status="approved" AND indents.project_id=projects.project_id AND indents.project_id IN ' + str(
                                     access_tuple) + '' \
                                    ' LEFT OUTER JOIN App_users on indents.created_by_user=App_users.user_id'
                cur.execute(indents_query)
                data=[]
                result = cur.fetchall()
                for i in result:
                    i = list(i)
                    if len(str(i[8]).strip()) > 0:
                        i[8] = str(i[8]).strip()
                        timestamp = datetime.strptime(i[8]+' 2022 +0530', '%A %d %B %H:%M %Y %z')
                        IST = pytz.timezone('Asia/Kolkata')
                        current_time = datetime.now(IST)
                        time_since_creation = current_time - timestamp
                        difference_in_seconds = time_since_creation.total_seconds()
                        difference_in_hours = difference_in_seconds // 3600
                        if difference_in_hours >= 24:
                            difference_in_days = difference_in_hours // 24
                            hours_remaining = difference_in_hours % 24
                            i[8] = str(int(difference_in_days)) + ' days, ' + str(
                                int(hours_remaining)) + 'hours'
                        else:
                            i[8] = str(int(difference_in_hours)) + ' hours'
                    data.append(i)
                return render_template('approved_indents.html', result=data)
        else:
            return 'You do not have access to view this page'

@app.route('/view_approved_POs', methods=['GET'])
def view_approved_POs():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_approved_POs'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'QS Head', 'QS Engineer','Purchase Executive','Purchase Head']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        current_user_role = session['role']
        if current_user_role in ['Super Admin', 'COO', 'QS Head', 'QS Engineer', 'Purchase Head']:
            indents_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                            ', App_users.name, indents.timestamp FROM indents INNER JOIN projects on indents.status="po_uploaded" AND indents.project_id=projects.project_id ' \
                            ' LEFT OUTER JOIN App_users on indents.created_by_user=App_users.user_id'

            cur.execute(indents_query)
            data = []
            result = cur.fetchall()
            for i in result:
                i = list(i)
                if len(str(i[8]).strip()) > 0:
                    i[8] = str(i[8]).strip()
                    timestamp = datetime.strptime(i[8] + ' 2022 +0530', '%A %d %B %H:%M %Y %z')
                    IST = pytz.timezone('Asia/Kolkata')
                    current_time = datetime.now(IST)
                    time_since_creation = current_time - timestamp
                    difference_in_seconds = time_since_creation.total_seconds()
                    difference_in_hours = difference_in_seconds // 3600
                    if difference_in_hours >= 24:
                        difference_in_days = difference_in_hours // 24
                        hours_remaining = difference_in_hours % 24
                        i[8] = str(int(difference_in_days)) + ' days, ' + str(
                            int(hours_remaining)) + 'hours'
                    else:
                        i[8] = str(int(difference_in_hours)) + ' hours'
                data.append(i)
            return render_template('approved_pos.html', result=data)
        elif current_user_role == 'Purchase Executive':
            current_user_email = session['email']
            access_query = 'SELECT access, role from App_users WHERE email=' + str(current_user_email)
            cur.execute(access_query)
            res = cur.fetchone()
            access = res[0]
            if len(access):
                access = access.split(',')
                access_as_int = [int(i) for i in access]
                access_tuple = tuple(access_as_int)
                indents_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                                ', App_users.name, indents.timestamp, indents.purchase_order FROM indents INNER JOIN projects on indents.status="po_uploaded" AND indents.project_id=projects.project_id AND indents.project_id IN ' + str(
                                     access_tuple) + '' \
                                    ' LEFT OUTER JOIN App_users on indents.created_by_user=App_users.user_id'
                cur.execute(indents_query)
                data=[]
                result = cur.fetchall()
                for i in result:
                    i = list(i)
                    if len(str(i[8]).strip()) > 0:
                        i[8] = str(i[8]).strip()
                        timestamp = datetime.strptime(i[8]+' 2022 +0530', '%A %d %B %H:%M %Y %z')
                        IST = pytz.timezone('Asia/Kolkata')
                        current_time = datetime.now(IST)
                        time_since_creation = current_time - timestamp
                        difference_in_seconds = time_since_creation.total_seconds()
                        difference_in_hours = difference_in_seconds // 3600
                        if difference_in_hours >= 24:
                            difference_in_days = difference_in_hours // 24
                            hours_remaining = difference_in_hours % 24
                            i[8] = str(int(difference_in_days)) + ' days, ' + str(
                                int(hours_remaining)) + 'hours'
                        else:
                            i[8] = str(int(difference_in_hours)) + ' hours'
                    data.append(i)
                return render_template('approved_pos.html', result=data)
        else:
            return 'You do not have access to view this page'

@app.route('/view_indent_details', methods=['GET'])
def view_indent_details():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/view_indent_details'
        return redirect('/erp/login')
    if request.method == 'GET':
        indent_id = request.args['indent_id']
        cur = mysql.connection.cursor()
        indents_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                        ', App_users.name, indents.timestamp, indents.purchase_order FROM indents INNER JOIN projects on indents.id='+str(indent_id)+' AND indents.project_id=projects.project_id ' \
                        ' LEFT OUTER JOIN App_users on indents.created_by_user=App_users.user_id'
        cur.execute(indents_query)
        result = cur.fetchone()
        return render_template('view_indent_details.html', result=result)


@app.route('/upload_po_for_indent', methods=['POST'])
def upload_po_for_indent():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/create_bill'
        return redirect('/erp/login')
    if request.method == 'POST':
        indent_id = request.form['indent_id']
        if 'purchase_order' in request.files:
            file = request.files['purchase_order']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                output = send_to_s3(file, app.config["S3_BUCKET"], filename)
                if output != 'success':
                    flash('File upload failed', 'danger')
                    return redirect(request.referrer)
                cur = mysql.connection.cursor()
                query = 'UPDATE indents set status=%s, purchase_order=%s WHERE id=%s'
                values = ('po_uploaded', str(indent_id)+'_'+filename, indent_id )
                cur.execute(query, values)
                mysql.connection.commit()

                get_indent_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                                ', indents.timestamp, indents.created_by_user, indents.acted_by_user FROM indents INNER JOIN projects on indents.project_id=projects.project_id ' \
                                ' AND indents.id='+str(indent_id)
                cur.execute(get_indent_query)
                result = cur.fetchone()
                if result is not None:
                    notification_body = 'PO uploaded for indent with id '+str(indent_id)+'. Details: '+str(result[4])+' '+str(result[5])+' '+str(result[3])+' For project '+str(result[2])
                    IST = pytz.timezone('Asia/Kolkata')
                    datetime_ist = datetime.now(IST)
                    timestamp = datetime_ist.strftime('%A %d %B %H:%M')
                    send_app_notification('PO Uploaded', notification_body, str(result[8]), str(result[8]), 'PO uploads', timestamp)
                    send_app_notification('PO Uploaded', notification_body, str(result[9]), str(result[9]), 'PO uploads', timestamp)
                flash('PO Uploaded successfully','success')
        return redirect('/erp/view_indent_details?indent_id='+str(indent_id))

@app.route('/sign_wo', methods=['GET', 'POST'])
def sign_wo():
    if request.method == 'GET':
        if 'wo_id' in request.args:
            work_order_query = 'SELECT p.project_name, p.project_number, wo.trade, wo.value, wo.contractor_name,' \
                               'wo.contractor_pan, wo.contractor_code, wo.contractor_address, wo.wo_number, wo.cheque_no' \
                               ' FROM work_orders wo ' \
                               'INNER JOIN projects p on p.project_id=wo.project_id AND wo.signed=0 AND wo.id=' + str(
                request.args['wo_id'])
            cur = mysql.connection.cursor()
            cur.execute(work_order_query)
            result = cur.fetchone()
        return render_template('sign_wo.html', wo=result, wo_id=str(request.args['wo_id']))

@app.route('/upload_signed_wo', methods=['POST'])
def upload_signed_wo():
    wo_id = request.form['wo_id']
    cur = mysql.connection.cursor()
    query = 'UPDATE work_orders SET signed=1 WHERE id='+wo_id
    cur.execute(query)
    mysql.connection.commit()
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            flash('Work order signed!','success')
            output = send_to_s3(file, app.config["S3_BUCKET"], 'work_order_'+str(wo_id)+'.pdf')
            if output != 'success':
                flash('File upload failed', 'danger')
                return redirect(request.referrer)
            return 'success'



@app.route('/approve_wo', methods=['GET', 'POST'])
def approve_wo():
    if request.method == 'GET':
        if 'wo_id' in request.args:
            work_order_query = 'SELECT p.project_name, p.project_number, wo.trade, wo.value, wo.contractor_name,' \
                               'wo.contractor_pan, wo.contractor_code, wo.contractor_address, wo.wo_number, wo.cheque_no' \
                               ' FROM work_orders wo ' \
                             'INNER JOIN projects p on p.project_id=wo.project_id AND wo.signed=1 AND wo.approved=0 AND wo.id='+str(request.args['wo_id'])
            cur = mysql.connection.cursor()
            cur.execute(work_order_query)
            result = cur.fetchone()
        return render_template('approve_wo.html', wo=result, wo_id=str(request.args['wo_id']))
    else:
        wo_id = request.form['wo_id']
        cur = mysql.connection.cursor()
        query = 'UPDATE work_orders SET approved=1 WHERE id=' + wo_id
        cur.execute(query)
        mysql.connection.commit()
        flash('Work order approved!', 'success')
        return redirect('/erp/view_unapproved_work_order')


@app.route('/archive_project', methods=['GET'])
def archive_project():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/create_project'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'Sales Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if 'project_id' in request.args:
        cur = mysql.connection.cursor()
        query = 'UPDATE projects set archived=1 WHERE project_id='+str(request.args['project_id'])
        cur.execute(query)
        mysql.connection.commit()
        flash('Project archived', 'warning')
        return redirect(request.referrer)
    else:
        flash('Missing fields', 'danger')
        return redirect(request.referrer)

@app.route('/unarchive_project', methods=['GET'])
def unarchive_project():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/create_project'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'Sales Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if 'project_id' in request.args:
        cur = mysql.connection.cursor()
        query = 'UPDATE projects set archived=0 WHERE project_id='+str(request.args['project_id'])
        cur.execute(query)
        mysql.connection.commit()
        flash('Project unarchived', 'success')
        return redirect(request.referrer)
    else:
        flash('Missing fields', 'danger')
        return redirect(request.referrer)


@app.route('/create_project', methods=['GET','POST'])
def create_project():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/create_project'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'Sales Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        sales_executives_query = 'SELECT user_id, name from App_users WHERE role="Sales Executive"'
        cur.execute(sales_executives_query)
        result = cur.fetchall()
        return render_template('create_project.html', sales_executives=result)
    else:

        column_names = list(request.form.keys())
        values = list(request.form.values())
        cur = mysql.connection.cursor()
        new_project_query = 'INSERT into projects'+str(tuple(column_names)).replace("'","")+'values '+str(tuple(values))
        cur.execute(new_project_query)
        project_id = cur.lastrowid
        cost_sheet_filename = ''
        site_inspection_report_filename = ''
        if 'cost_sheet' in request.files:
            file = request.files['cost_sheet']
            if file.filename == '':
                flash('No selected file', 'danger ')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                cost_sheet_filename = 'cost_sheet_'+str(project_id)+'_'+filename
                output = send_to_s3(file, app.config["S3_BUCKET"], cost_sheet_filename)
                if output != 'success':
                    flash('File upload failed', 'danger')
                    return redirect(request.referrer)


        if 'site_inspection_report' in request.files:
            file = request.files['site_inspection_report']
            if file.filename == '':
                flash('No selected file', 'danger ')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                site_inspection_report_filename = 'site_inspection_report_'+str(project_id)+'_'+filename
                output = send_to_s3(file, app.config["S3_BUCKET"], site_inspection_report_filename)
                if output != 'success':
                    flash('File upload failed', 'danger')
                    return redirect(request.referrer)

        update_filename_query = 'UPDATE projects set cost_sheet=%s, site_inspection_report=%s WHERE project_id=%s'
        cur.execute(update_filename_query, (cost_sheet_filename, site_inspection_report_filename, str(project_id)))
        flash('Project created successfully', 'success')
        mysql.connection.commit()
        return redirect(request.referrer)

@app.route('/edit_project', methods=['GET','POST'])
def edit_project():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/edit_project'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin', 'COO', 'Sales Executive']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        fields_as_string = ", ".join(project_fields)
        get_details_query = 'SELECT ' + fields_as_string + ' from projects WHERE project_id=' + str(
            request.args['project_id'])
        cur = mysql.connection.cursor()
        cur.execute(get_details_query)
        result = cur.fetchone()
        project = projects(*result)
        sales_executives_query = 'SELECT user_id, name from App_users WHERE role="Sales Executive"'
        cur.execute(sales_executives_query)
        result = cur.fetchall()
        return render_template('edit_project.html', p=project, sales_executives=result)
    else:

        column_names = list(request.form.keys())

        update_string = ""
        for i in column_names[:-1]:
            if request.form[i].strip() != '':
                update_string += i+'="'+request.form[i] +'", '
        # Remove the last comma
        update_string = update_string[:-2]
        update_project_query = 'UPDATE projects SET '+update_string+' WHERE project_id='+str(request.form['project_id'])
        cur = mysql.connection.cursor()
        cur.execute(update_project_query)
        mysql.connection.commit()
        cost_sheet_filename = ''
        site_inspection_report_filename = ''
        if 'cost_sheet' in request.files:
            file = request.files['cost_sheet']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                cost_sheet_filename = 'cost_sheet_' + str(request.form['project_id']) + '_' + filename
                output = send_to_s3(file, app.config["S3_BUCKET"], cost_sheet_filename)
                if output == 'success':
                    update_filename_query = 'UPDATE projects set cost_sheet=%s WHERE project_id=%s'
                    cur.execute(update_filename_query,
                                (cost_sheet_filename, str(request.form['project_id'])))

        if 'site_inspection_report' in request.files:
            file = request.files['site_inspection_report']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                site_inspection_report_filename = 'site_inspection_report_' + str(request.form['project_id']) + '_' + filename
                output = send_to_s3(file, app.config["S3_BUCKET"], site_inspection_report_filename)
                if output == 'success':
                    update_filename_query = 'UPDATE projects set site_inspection_report=%s WHERE project_id=%s'
                    cur.execute(update_filename_query,
                                (site_inspection_report_filename, str(request.form['project_id'])))

        mysql.connection.commit()
        flash('Project updated successfully', 'success')
        return redirect('/erp/view_project_details?project_id=' + str(request.form['project_id']))

        # This has to be checked. The if condition is returning false even when everything is okay
        # if cur.rowcount == 1:
        #     flash('Project updated successfully', 'success')
        #     return redirect('/erp/view_project_details?project_id=' + str(request.form['project_id']))
        # else:
        #     flash('Project not updated', 'danger')
        #     return redirect(request.referrer)

@app.route('/unapproved_projects', methods=['GET'])
def unapproved_projects():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/unapproved_projects'
        return redirect('/erp/login')
    if session['role'] not in ['Super Admin']:
        flash('You do not have permission to view that page', 'danger')
        return redirect(request.referrer)
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        unapproved_projects_query = 'SELECT project_id, project_name, project_number from projects WHERE is_approved=0 AND archived=0 ORDER BY project_number'
        cur.execute(unapproved_projects_query)
        result = cur.fetchall()
        return render_template('unapproved_projects.html', projects=result)

@app.route('/projects', methods=['GET'])
def approved_projects():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/projects'
        return redirect('/erp/login')
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        result = []
        if len(session['projects']) > 0:
            if session['role'] not in ['Super Admin','COO','QS Head','Site Engineer','Purchase Head','Sales Executive']:
                approved_projects_query = 'SELECT project_id, project_name, project_number from projects WHERE is_approved=1 AND archived=0 ' \
                                          'AND project_id IN '+str(session['projects'])+' ORDER BY project_number'
                cur.execute(approved_projects_query)
                result = cur.fetchall()
            else:
                approved_projects_query = 'SELECT project_id, project_name, project_number from projects WHERE is_approved=1 AND archived=0 ORDER BY project_number'
                cur.execute(approved_projects_query)
                result = cur.fetchall()
        return render_template('approved_projects.html', projects=result)

@app.route('/archived_projects', methods=['GET'])
def archived_projects():
    if 'email' not in session:
        flash('You need to login to continue', 'danger')
        session['last_route'] = '/erp/projects'
        return redirect('/erp/login')
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        result = []
        if len(session['projects']) > 0:
            if session['role'] not in ['Super Admin','COO','QS Head','Site Engineer','Purchase Head']:
                archived_projects_query = 'SELECT project_id, project_name, project_number from projects WHERE is_approved=1 AND archived=1 ' \
                                          'AND project_id IN '+str(session['projects'])+' ORDER BY project_number'
                cur.execute(archived_projects_query)
                result = cur.fetchall()
            else:
                archived_projects_query = 'SELECT project_id, project_name, project_number from projects WHERE is_approved=1 AND archived=1 ORDER BY project_number'
                cur.execute(archived_projects_query)
                result = cur.fetchall()
        return render_template('archived_projects.html', projects=result)

@app.route('/view_project_details',methods=['GET'])
def view_project_details():
    if request.method == 'GET':
        fields = [
            'project_name','project_number', 'project_location','package_type', 'no_of_floors', 'project_value', 'date_of_initial_advance', 'date_of_agreement', 'sales_executive', 'site_area',
            'gf_slab_area', 'ff_slab_area', 'sf_slab_area', 'tf_slab_area', 'tef_slab_area', 'shr_oht', 'elevation_details', 'additional_cost',
            'paid_percentage', 'comments', 'cost_sheet', 'site_inspection_report', 'is_approved', 'archived'
        ]
        fields_as_string = ", ".join(fields)
        get_details_query = 'SELECT '+fields_as_string+' from projects WHERE project_id='+str(request.args['project_id'])
        cur = mysql.connection.cursor()
        cur.execute(get_details_query)
        result = cur.fetchone()
        details = {}

        sales_executive_query = 'SELECT name from App_users WHERE user_id='+str(result[8])
        cur.execute(sales_executive_query)
        sales_executive_query_result = cur.fetchone()
        for i in range (len(fields) - 1) :
            fields_name_to_show = " ".join(fields[i].split('_')).title()
            if fields_name_to_show == 'Sales Executive':
                details[fields_name_to_show] = sales_executive_query_result[0]
            else:
                details[fields_name_to_show] = result[i]
        return render_template('view_project_details.html', details=details, approved=str(result[-2]), archived=str(result[-1]))

@app.route('/approve_project', methods=['GET'])
def approve_project():
    project_id = request.args['project_id']
    approve_project_query = 'UPDATE projects set is_approved="1" WHERE project_id='+str(project_id)
    cur = mysql.connection.cursor()
    cur.execute(approve_project_query)
    mysql.connection.commit()
    flash('Project has been approved', 'success')
    return redirect('/erp/view_project_details?project_id='+str(project_id))

@app.route('/projects_with_no_design_team', methods=['GET'])
def projects_with_no_design_team():
    no_design_team_query = 'SELECT P.project_id, P.project_name from projects P left join project_design_team PDT ' \
                           'on P.project_id = PDT.project_id WHERE P.is_approved=1 AND P.archived=0 AND PDT.project_id is NULL'
    cur = mysql.connection.cursor()
    cur.execute(no_design_team_query)
    result = cur.fetchall()
    return render_template('projects_with_no_design_team.html', projects=result)

@app.route('/projects_with_design_team', methods=['GET'])
def projects_with_design_team():
    design_team_query = 'SELECT P.project_id, P.project_name from projects P left join project_design_team PDT ' \
                        'on P.project_id = PDT.project_id WHERE P.is_approved=1 AND P.archived=0 AND PDT.project_id is NOT NULL'
    cur = mysql.connection.cursor()
    cur.execute(design_team_query)
    result = cur.fetchall()
    return render_template('projects_with_design_team.html', projects=result)

@app.route('/projects_with_no_operations_team', methods=['GET'])
def projects_with_no_operations_team():
    no_ops_team_query = 'SELECT P.project_id, P.project_name from projects P left join project_operations_team POT ' \
                        'on P.project_id = POT.project_id WHERE P.is_approved=1 AND P.archived=0 AND POT.project_id is NULL'
    cur = mysql.connection.cursor()
    cur.execute(no_ops_team_query)
    result = cur.fetchall()
    return render_template('projects_with_no_operations_team.html', projects=result)

@app.route('/projects_with_operations_team', methods=['GET'])
def projects_with_operations_team():
    ops_team_query = 'SELECT P.project_id, P.project_name from projects P left join project_operations_team POT ' \
                     'on P.project_id = POT.project_id WHERE P.is_approved=1 AND P.archived=0 AND POT.project_id is NOT NULL'
    cur = mysql.connection.cursor()
    cur.execute(ops_team_query)
    result = cur.fetchall()
    return render_template('projects_with_operations_team.html', projects=result)

@app.route('/assign_design_team', methods=['GET','POST'])
def assign_design_team():
    if request.method == 'GET':
        design_team_query = 'SELECT user_id, name, role from App_users WHERE role="Architect" OR role="Senior Architect" OR role="Structural Designer" OR role="Electrical Designer" OR role="PHE Designer"'
        cur = mysql.connection.cursor()
        cur.execute(design_team_query)
        architects = []
        structural_designers = []
        electrical_designers = []
        phe_designers = []
        senior_architects = []
        result = cur.fetchall()
        for i in result:
            if i[2] == 'Architect':
                architects.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Structural Designer':
                structural_designers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Electrical Designer':
                electrical_designers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'PHE Designer':
                phe_designers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Senior Architect':
                senior_architects.append({'id': i[0], 'name': i[1]})
        return render_template('assign_design_team.html',senior_architects=senior_architects,  architects=architects, structural_designers=structural_designers, electrical_designers=electrical_designers, phe_designers=phe_designers)
    else:
        column_names = list(request.form.keys())
        values = list(request.form.values())

        cur = mysql.connection.cursor()
        assign_design_team_query = 'INSERT into project_design_team' + str(tuple(column_names)).replace("'", "") + 'values ' + str(
            tuple(values))
        cur.execute(assign_design_team_query)
        mysql.connection.commit()
        flash('Design team has been assigned successfully', 'success')
        return redirect('/erp/projects_with_design_team')

@app.route('/edit_design_team', methods=['GET','POST'])
def edit_design_team():
    if request.method == 'GET':
        if 'project_id' not in request.args:
            flash('Missing fields', 'danger')
            return redirect('/erp/projects_with_no_design_team')
        project_id = request.args['project_id']
        design_team_query = 'SELECT user_id, name, role from App_users WHERE role="Architect" OR role="Senior Architect" OR role="Structural Designer" OR role="Electrical Designer" OR role="PHE Designer"'
        cur = mysql.connection.cursor()
        cur.execute(design_team_query)
        architects = []
        structural_designers = []
        electrical_designers = []
        phe_designers = []
        senior_architects = []
        result = cur.fetchall()
        for i in result:
            if i[2] == 'Architect':
                architects.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Structural Designer':
                structural_designers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Electrical Designer':
                electrical_designers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'PHE Designer':
                phe_designers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Senior Architect':
                senior_architects.append({'id': i[0], 'name': i[1]})
        existing_team_query = 'SELECT * FROM project_design_team WHERE project_id='+str(project_id)
        cur.execute(existing_team_query)
        res = cur.fetchone()
        existing_team = {
            'Architect': res[2],
            'Structural Designer': res[3],
            'Electrical Designer': res[4],
            'PHE Designer': res[5],
            'Senior Architect': res[6]
        }

        return render_template('edit_design_team.html',existing_team=existing_team, senior_architects=senior_architects,  architects=architects, structural_designers=structural_designers, electrical_designers=electrical_designers, phe_designers=phe_designers)
    else:

        cur = mysql.connection.cursor()
        column_names = list(request.form.keys())

        update_string = ""
        for i in column_names[:-1]:
            if request.form[i].strip() != '':
                update_string += i + '="' + request.form[i] + '", '
        # Remove the last comma
        update_string = update_string[:-2]
        update_project_query = 'UPDATE project_design_team SET ' + update_string + ' WHERE project_id=' + str(
            request.form['project_id'])


        cur.execute(update_project_query)
        mysql.connection.commit()
        flash('Design team has been updated successfully', 'success')
        return redirect('/erp/projects_with_design_team')

@app.route('/assign_operations_team', methods=['GET','POST'])
def assign_operations_team():
    if request.method == 'GET':

        operations_team_query = 'SELECT user_id, name, role from App_users WHERE role="Project Coordinator" OR role="Project Manager" OR role="Purchase Executive" OR role="QS Engineer"'
        cur = mysql.connection.cursor()
        cur.execute(operations_team_query)
        co_ordinators = []
        project_managers = []
        purchase_executives = []
        qs_engineers = []
        result = cur.fetchall()
        for i in result:
            if i[2] == 'Project Coordinator':
                co_ordinators.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Project Manager':
                project_managers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Purchase Executive':
                purchase_executives.append({'id': i[0], 'name': i[1]})
            if i[2] == 'QS Engineer':
                qs_engineers.append({'id': i[0], 'name': i[1]})

        return render_template('assign_operations_team.html', co_ordinators=co_ordinators, project_managers=project_managers, purchase_executives=purchase_executives, qs_engineers=qs_engineers)
    else:
        column_names = list(request.form.keys())
        values = list(request.form.values())

        cur = mysql.connection.cursor()
        assign_operations_team_query = 'INSERT into project_operations_team' + str(tuple(column_names)).replace("'", "") + 'values ' + str(
            tuple(values))
        cur.execute(assign_operations_team_query)
        mysql.connection.commit()
        flash('Operations team has been assigned successfully','success')
        return redirect('/erp/projects_with_operations_team')

@app.route('/edit_operations_team', methods=['GET','POST'])
def edit_operations_team():
    if request.method == 'GET':
        if 'project_id' not in request.args:
            flash('Missing fields', 'danger')
            return redirect('/erp/projects_with_no_operations_team')
        project_id = request.args['project_id']
        operations_team_query = 'SELECT user_id, name, role from App_users WHERE role="Project Coordinator" OR role="Project Manager" OR role="Purchase Executive" OR role="QS Engineer"'
        cur = mysql.connection.cursor()
        cur.execute(operations_team_query)
        co_ordinators = []
        project_managers = []
        purchase_executives = []
        qs_engineers = []
        result = cur.fetchall()
        for i in result:
            if i[2] == 'Project Coordinator':
                co_ordinators.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Project Manager':
                project_managers.append({'id': i[0], 'name': i[1]})
            if i[2] == 'Purchase Executive':
                purchase_executives.append({'id': i[0], 'name': i[1]})
            if i[2] == 'QS Engineer':
                qs_engineers.append({'id': i[0], 'name': i[1]})
        existing_team_query = 'SELECT * FROM project_operations_team WHERE project_id=' + str(project_id)
        cur.execute(existing_team_query)
        res = cur.fetchone()
        existing_team = {
            'Project Coordinator': res[2],
            'Project Manager': res[3],
            'Purchase Executive': res[4],
            'QS Engineer': res[5],
        }
        return render_template('edit_operations_team.html',existing_team=existing_team, co_ordinators=co_ordinators, project_managers=project_managers, purchase_executives=purchase_executives, qs_engineers=qs_engineers)
    else:
        cur = mysql.connection.cursor()
        column_names = list(request.form.keys())

        update_string = ""
        for i in column_names[:-1]:
            if request.form[i].strip() != '':
                update_string += i + '="' + request.form[i] + '", '
        # Remove the last comma
        update_string = update_string[:-2]
        update_project_query = 'UPDATE project_operations_team SET ' + update_string + ' WHERE project_id=' + str(
            request.form['project_id'])

        cur.execute(update_project_query)
        mysql.connection.commit()
        flash('Opeartions team has been updated successfully', 'success')
        return redirect('/erp/projects_with_operations_team')


@app.route('/revised_drawings', methods=['GET',"POST"])
def revised_drawings():
    if request.method == 'GET':
        projects = get_projects()
        drawings = []
        if 'project_id' in request.args:
            cur = mysql.connection.cursor()
            reviewed_drawings_query = 'SELECT id, type, name from revised_drawings WHERE project_id='+str(request.args['project_id'])
            cur.execute(reviewed_drawings_query)
            drawings = cur.fetchall()




        return render_template('revised_drawings.html', drawings=drawings, projects=projects)



@app.route('/upload_revised_drawing', methods=['GET',"POST"])
def upload_revised_drawing():
    if request.method == 'GET':
        projects = get_projects()
        drawing_types = ['Architect','Structural','Electrical','Plumbing']

        return render_template('upload_revised_drawing.html', projects=projects, drawing_types=drawing_types)
    else:
        cur = mysql.connection.cursor()
        project_id = request.form['project_id']
        type = request.form['drawing_type']
        name = request.form['drawing_name']
        new_drawing_query = 'INSERT into revised_drawings (name, type, project_id) values (%s, %s, %s)'
        cur.execute(new_drawing_query, (name, type, str(project_id)))
        drawing_id = cur.lastrowid
        if 'drawing' in request.files:
            file = request.files['drawing']
            if file.filename == '':
                flash('No selected file', 'danger ')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                drawing_filename = 'rd_'+str(drawing_id)+'.pdf'
                output = send_to_s3(file, app.config["S3_BUCKET"], drawing_filename)
                if output != 'success':
                    flash('File upload failed', 'danger')
                    return redirect(request.referrer)
            mysql.connection.commit()
            flash('Revised drawing uploaded successfully', 'success')
            return redirect('/erp/revised_drawings')

@app.route('/drawings', methods=['GET'])
def drawings():
    table_name = ''
    if 'category' in request.args:
        table_name = request.args['category']
    else:
        table_name = get_drwaings_table_name()
    session['category'] = table_name
    drawings_query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'"+table_name+"'"
    cur = mysql.connection.cursor()
    cur.execute(drawings_query)
    result = cur.fetchall()

    query_string = 'p.project_id, p.project_name, p.project_number, '

    drawing_names = []
    for i in result[2:]:
        query_string += 'd.' + i[0] + ', '
        drawing_names.append(i[0].replace('_',' ').capitalize())

    query_string = query_string[:-2]
    drawings = []
    if len(session['projects']) > 0:
        if session['role'] not in ['Super Admin','Purchase Head', 'COO', 'QS Head','Purchase Head', 'Site Engineer', 'Design Head']:
            drawings_info = "SELECT " + query_string + " FROM projects p LEFT OUTER JOIN " + table_name + " d on " \
                                  "p.project_id=d.project_id AND p.is_approved=1 AND p.archived=0" \
                                      ' WHERE p.project_id IN ' + str(session['projects'])

            cur.execute(drawings_info)
            drawings = cur.fetchall()

        else:
            drawings_info = "SELECT "+ query_string +" FROM projects p LEFT OUTER JOIN "+table_name+" d on " \
                        "p.project_id=d.project_id WHERE p.is_approved=1 AND p.archived=0"
            cur.execute(drawings_info)
            drawings = cur.fetchall()

    return render_template('drawings.html', role=session['role'], drawing_names=drawing_names, drawings=drawings)

def get_drwaings_table_name():
    role = session['role']
    if role in ['Super Admin','COO','Senior Architect','Architect','Design Head']:
        return 'architect_drawings'
    elif role == 'Structural Designer':
        return 'structural_drawings'
    elif role == 'Electrical Designer':
        return 'electrical_drawings'
    elif role == 'PHE Designer':
        return 'plumbing_drawings'

@app.route('/upload_drawing', methods=['POST'])
def upload_drawing():
    if request.method == 'POST':
        drawing_filename = ''
        if 'drawing' in request.files:
            file = request.files['drawing']
            if file.filename == '':
                flash('No selected file', 'danger ')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                drawing_filename = 'drawing_'+str(int(time.time()))+'.pdf'
                output = send_to_s3(file, app.config["S3_BUCKET"], drawing_filename)
                if output != 'success':
                    flash('File upload failed', 'danger')
                    return redirect(request.referrer)
        project_id = request.form['project_id']
        drawing_name = request.form['drawing_name']
        drawing_name = drawing_name.lower().replace(' ', '_')

        cur = mysql.connection.cursor()
        table_name = ''
        if 'category' in session:
            table_name = session['category']
        else:
            table_name = get_drwaings_table_name()
        check_if_drawing_exists_query = 'SELECT id FROM '+table_name+' WHERE project_id='+str(project_id)
        cur.execute(check_if_drawing_exists_query)
        result = cur.fetchone()
        if result is not None:
            update_drawing_query = 'UPDATE '+table_name+' set '+drawing_name+'="'+drawing_filename+'" WHERE id='+str(result[0])
            cur.execute(update_drawing_query)
            mysql.connection.commit()
            flash('Drawing uploaded!', 'success')
            return redirect('/erp/drawings')
        else:
            insert_drawing_query = 'INSERT into '+table_name+' (project_id, '+drawing_name+') values (%s, %s)'
            cur.execute(insert_drawing_query, (str(project_id), drawing_filename))
            mysql.connection.commit()
            flash('Drawing uploaded!', 'success')
            return redirect('/erp/drawings')

@app.route('/mark_drawing_in_progress', methods=['POST'])
def mark_drawing_in_progress():
    project_id = request.form['project_id']
    drawing_name = request.form['drawing_name']
    drawing_name = drawing_name.lower().replace(' ', '_')

    cur = mysql.connection.cursor()
    table_name = ''
    if 'category' in session:
        table_name = session['category']
    else:
        table_name = get_drwaings_table_name()

    cur = mysql.connection.cursor()
    check_if_drawing_exists_query = 'SELECT id FROM '+table_name+'  WHERE project_id=' + str(project_id)
    cur.execute(check_if_drawing_exists_query)
    result = cur.fetchone()
    if result is not None:
        update_drawing_query = 'UPDATE '+table_name+' set ' + drawing_name + '="0" WHERE id=' + str(
            result[0])
        cur.execute(update_drawing_query)
        mysql.connection.commit()
        flash('Drawing marked as in progress!', 'success')
        return redirect('/erp/drawings')
    else:
        insert_drawing_query = 'INSERT into '+table_name+' (project_id, ' + drawing_name + ') values (%s, %s)'
        cur.execute(insert_drawing_query, (str(project_id), '0'))
        mysql.connection.commit()
        flash('Drawing marked as in progress!', 'success')
        return redirect('/erp/drawings')

@app.route('/logout', methods=['GET'])
def logout():
    del session['email']
    del session['name']
    del session['role']
    return redirect('/erp/login')



# APIs for mobile app
@app.route('/API/create_indent', methods=['POST'])
def create_indent():
    if request.method == 'POST':
        project_id = request.form['project_id']
        material = request.form['material']
        quantity = request.form['quantity']
        unit = request.form['unit']
        purpose = request.form['purpose']
        timestamp = request.form['timestamp']
        status = 'unapproved'
        cur = mysql.connection.cursor()
        user_id = request.form['user_id']
        query = 'INSERT into indents(project_id, material, quantity, unit, purpose, status, created_by_user, timestamp) values (%s, %s, %s, %s, %s, %s, %s, %s)'
        values = (project_id, material, quantity, unit, purpose, status, user_id, timestamp)
        cur.execute(query, values)
        mysql.connection.commit()
        return jsonify({'message':'success'})

def save_notification_to_db(title, body, user_id, role, category, timestamp):
    cur = mysql.connection.cursor()
    notification_query = 'INSERT into app_notifications(title, body, user_id, role, category, timestamp) values (%s, %s, %s, %s, %s, %s)'
    values = (title, body, user_id, role, category, timestamp)
    cur.execute(notification_query, values)
    mysql.connection.commit()
    return

def send_app_notification(title, body, user_id, role, category, timestamp):
    save_notification_to_db(title, body, user_id, role, category, timestamp)
    recipient = ''
    if str(user_id).strip() == '':
        recipient = role
    else:
        recipient = user_id
    url = 'https://fcm.googleapis.com/fcm/send'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key=AAAAlQ1Lrfw:APA91bHvI2-qFZNCf-oFfeZgM0JUDxxbuykH_ffka9hPUE0xBpiza4uHF0LmItT_SfMZ1Zl5amGUfAXigaR_VcMsEArqpOwHNup4oRTQ24htJ_GWYH0OWZzFrH2lRY24mnQ-uiHgLyln'
    }
    data = {
        "notification": {"title": title, "body": body, 'data': {'category': 'team_notifications'}},
        "to": "/topics/" + recipient,
    }
    requests.post(url, headers=headers, data=json.dumps(data))
    return

@app.route('/API/change_indent_status', methods=['POST'])
def change_indent_status():
    indent_id = request.form['indent_id']
    status = request.form['status']

    cur = mysql.connection.cursor()
    query = 'UPDATE indents SET status="'+status+'", acted_by_user='+str(request.form['acted_by_user'])+' WHERE id='+str(indent_id)
    cur.execute(query)
    mysql.connection.commit()

    if status == 'approved':
        send_app_notification(
            'Indent Approved',
            request.form['notification_body'],
            request.form['user_id'],
            request.form['user_id'],
            'Indent Approval',
            request.form['timestamp']
        )
    elif status == 'rejected':
        send_app_notification(
            'Indent Rejected',
            request.form['notification_body'],
            request.form['user_id'],
            request.form['user_id'],
            'Indent Rejection',
            request.form['timestamp']
        )
    return jsonify({'message': 'success'})

@app.route('/API/edit_and_approve_indent', methods=['POST'])
def edit_and_approve_indent():
    indent_id = request.form['indent_id']
    status = 'approved'
    project_id = request.form['project_id']
    material = request.form['material']
    quantity = request.form['quantity']
    user_id = request.form['acted_by_user']
    unit = request.form['unit']
    purpose = request.form['purpose']
    cur = mysql.connection.cursor()
    query = 'UPDATE indents SET status=%s, project_id=%s, material=%s, quantity=%s, unit=%s, purpose=%s, acted_by_user=%s WHERE id=%s'
    values = (status, project_id, material, quantity, unit, purpose, user_id, indent_id)
    cur.execute(query, values)
    mysql.connection.commit()
    send_app_notification(
        'Indent Approved',
        request.form['notification_body'],
        request.form['user_id'],
        request.form['user_id'],
        'Indent Approval',
        request.form['timestamp']
    )
    return jsonify({'message': 'success'})

@app.route('/API/get_unapproved_indents', methods=['GET'])
def get_unapproved_indents():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        user_id = request.args['user_id']
        access_query = 'SELECT access, role from App_users WHERE user_id='+str(user_id)
        cur.execute(access_query)
        res = cur.fetchone()
        access = res[0]
        role = res[1]
        if role == 'Admin':
            indents_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                            ', App_users.name, indents.timestamp, indents.created_by_user FROM indents INNER JOIN projects on indents.status="unapproved" AND indents.project_id=projects.project_id '\
                                ' LEFT OUTER JOIN App_users on indents.created_by_user=App_users.user_id'
            cur.execute(indents_query)
            res = cur.fetchall()
            data = []
            for i in res:
                indent_entry = {}
                indent_entry['id'] = i[0]
                indent_entry['project_id'] = i[1]
                indent_entry['project_name'] = i[2]
                indent_entry['material'] = i[3]
                indent_entry['quantity'] = i[4]
                indent_entry['unit'] = i[5]
                indent_entry['purpose'] = i[6]
                indent_entry['created_by_user'] = i[7]
                indent_entry['timestamp'] = i[8]
                indent_entry['created_by_user_id'] = i[9]
                data.append(indent_entry)

            return jsonify(data)
        elif len(access):
            access = access.split(',')
            access_as_int = [int(i) for i in access]
            access_tuple = tuple(access_as_int)
            indents_query = 'SELECT indents.id, projects.project_id, projects.project_name, indents.material, indents.quantity, indents.unit, indents.purpose' \
                            ', App_users.name, indents.timestamp, indents.created_by_user FROM indents INNER JOIN projects on indents.status="unapproved" AND indents.project_id=projects.project_id AND indents.project_id IN '+str(access_tuple)+'' \
                            ' LEFT OUTER JOIN App_users on indents.created_by_user=App_users.user_id'
            cur.execute(indents_query)
            res = cur.fetchall()
            data = []
            for i in res:
                indent_entry = {}
                indent_entry['id'] = i[0]
                indent_entry['project_id'] = i[1]
                indent_entry['project_name'] = i[2]
                indent_entry['material'] = i[3]
                indent_entry['quantity'] = i[4]
                indent_entry['unit'] = i[5]
                indent_entry['purpose'] = i[6]
                indent_entry['created_by_user'] = i[7]
                indent_entry['timestamp'] = i[8]
                indent_entry['created_by_user_id'] = i[9]
                data.append(indent_entry)

            return jsonify(data)
        else: return jsonify([])

@app.route('/API/get_notifications', methods = ['GET'])
def get_notifications():
    recipient = request.args['recipient']
    cur = mysql.connection.cursor()
    notifications_query = 'SELECT title, body, timestamp from app_notifications WHERE user_id='+str(recipient)
    cur.execute(notifications_query)
    data = []
    result = cur.fetchall()
    for i in result:
        data.append({'title': i[0], 'body': i[1], 'timestamp': i[2]})
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)