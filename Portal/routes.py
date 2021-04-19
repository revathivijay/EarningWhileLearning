from Portal.forms import SubmitResearchWork, VerifyReport, LoginForm, UpdateResearchWork, VerifyPublication, CreateJob, \
    GradeJob
from Portal.__init__ import csv_file
from werkzeug.utils import secure_filename
import hashlib  # for SHA512
from flask_login import login_user, current_user, logout_user, login_required
import requests
import random
import os
import shutil
from bson.objectid import ObjectId
from bson import json_util
from flask import Flask, render_template, url_for, request, session, redirect, send_from_directory, jsonify, flash
from flask_pymongo import PyMongo, MongoClient
import bcrypt
import os.path
import datetime

import datetime

import datetime

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'earn_while_learn'
app.config['STATIC_FOLDER'] = '/Portal/static/'
app.config[
    'MONGO_URI'] = 'mongodb+srv://taklu:taklu@cluster0.cut8t.mongodb.net/earn_while_learn?retryWrites=true&w=majority'
app.secret_key = 'hi'

mongo = PyMongo(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
print(APP_ROOT)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = LoginForm(request.form)
    # if 'username' in session:
    #     print("IN Session")
    #     return redirect('/')

    if request.method == 'POST':
        print("using db")
        users = mongo.db.students
        user_id = request.form.get('id')
        user_email = request.form.get('email')
        print(user_id, user_email)

        print("search for user")
        existing_user = users.find_one({'id': user_id})
        if existing_user is None:
            print("user doesn't exist")
            hashpass = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())
            users.insert(
                {'id': user_id,
                 'email': user_email,
                 'password': hashpass})

            session['username'] = "Eshita"

            print('go home')
            return redirect('/')

        print('user exists')
        return render_template('register.html', msg="The username is taken, please enter a different username",
                               form=form)

    print('send to signup')
    return render_template('register.html', msg="", form=form)


@app.route('/register_staff', methods=['POST', 'GET'])
def register_staff():
    form = LoginForm(request.form)
    if 'username' in session:
        print("IN Session")
        return redirect('/')

    if request.method == 'POST':
        print("using db")
        users = mongo.db.staff
        user_id = request.form.get('id')
        user_email = request.form.get('email')
        print(user_id, user_email)

        print("search for user")
        existing_user = users.find_one({'id': user_id})
        if existing_user is None:
            print("user doesn't exist")
            hashpass = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())
            users.insert(
                {'id': user_id,
                 'email': user_email,
                 'password': hashpass})

            session['username'] = "Prof. Murli"

            print('go home')
            return redirect('/')

        print('user exists')
        return render_template('register_staff.html', msg="The username is taken, please enter a different username",
                               form=form)

    print('send to signup')
    return render_template('register_staff.html', msg="", form=form)


def get_student_name(s_id):
    s_name = mongo.db.students.find_one({'id': s_id})
    s_name = s_name['name']['fname'] + " " + s_name['name']['lname']
    return s_name


def get_user_type(id):
    print(id)
    user = mongo.db.userType.find_one({'id': id})
    print("User: ", user)
    return user['type']


@app.route('/add_project', methods=['POST', 'GET'])
def add_project():
    print("In /add_project")
    submit_work_form = SubmitResearchWork(request.form)
    update_work_form = UpdateResearchWork(request.form)

    s_id = session['id'] if session['id'] else ""
    s_name = get_student_name(s_id)
    user_type = get_user_type(s_id)

    if request.method == 'POST':
        print("using db")
        research = mongo.db.research
        user_id_students = request.form.get('students')
        user_id_staff = request.form.get('staff')
        project_topic = request.form.get('topic')
        departments_involved = request.form.get('departments')

        print(user_id_students, user_id_staff, project_topic, departments_involved)

        if user_id_students is not None:
            print("#### inserting project ####")
            research.insert(
                {
                    'students': user_id_students.split(","),
                    'staff': user_id_staff.split(","),
                    'topic': project_topic,
                    'departments': departments_involved.split(","),
                    'isPublished': False,
                    'publicationDOI': None,
                    'publicationJournal': None,
                    'filelist': {},
                    'date_started': datetime.datetime.today()
                }
            )

            print('Project inserted!')
            my_projects, topic_list, filelists = get_project_lists()
            total = len(my_projects)

            return render_template('add_project.html', msg="", submit_work_form=submit_work_form,
                                   update_work_form=update_work_form, my_projects=my_projects, topic_list=topic_list,
                                   filelists=filelists, total=total, s_name=s_name, user_type=user_type)
    else:
        print('In else of add project')
        return render_template('add_project.html', msg="", submit_work_form=submit_work_form,
                               update_work_form=update_work_form, my_projects=[], topic_list=[],
                               filelists=[], total=0, s_name=s_name, user_type=user_type)


@app.route('/update_project/<id>', methods=['POST', 'GET'])
def update_project(id):

    print("In update project")

    s_id = session['id'] if session['id'] else "171071045"
    s_name = get_student_name(s_id)
    user_type = get_user_type(s_id)

    submit_work_form = SubmitResearchWork(request.form)
    update_work_form = UpdateResearchWork(request.form)

    # project = mongo.db.research.find_one({"_id": ObjectId(id)})

    # if request.method == 'POST':
    target = os.path.join(APP_ROOT, 'static/documents')  # folder path
    print("Target: ", target)
    if not os.path.isdir(target):
        os.mkdir(target)  # create folder if not exits
    my_projects, topic_list, filelist = get_project_lists()
    print("Initial filelist (all projects): ", filelist)

    files = []
    test = request.files.getlist('Document')
    print("TEST: ", test)

    for upload in request.files.getlist("Document"):  # multiple image handle
        print("upload: ", upload)
        filename = secure_filename(upload.filename)
        destination = "/".join([target, filename])
        print("file dest: ", destination)
        upload.save(destination)
        print("file saved")
        # research.insert({'filelist': filename})
        print(filename, "ho gayi upload")
        files.append({filename: False})
        break

    print("filessss: ", files)

    # if file was uploaded
    if len(files) != 0:
        mongo.db.research.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {"filelist": files[0]}
            }
        )
        print("Updated in research")

        # inserting in reports collection
        mongo.db.reports.insert_one(
            {
                "projectID": ObjectId(id),
                "reportName": filename,
                "date_submitted": datetime.datetime.today(),
                "effort": None,
                "novelty": None,
                "relevance": None
             }
        )
        print("Inserted in reports")

    project = mongo.db.research.find_one({'_id': ObjectId(id)})
    filelist = project['filelist']

    print("DBs Updated")


    return render_template('update_project.html', project=project, total=len(filelist), filelist=filelist,
                           my_projects=my_projects, update_work_form=update_work_form,
                           submit_work_form=submit_work_form, topic_list=topic_list, s_name=s_name,
                           user_type=user_type)


@app.route('/view_projects/<user_type>')
def view_projects(user_type):
    if user_type == 'student':
        s_id = session['id'] if session['id'] else "171071045"
        s_username = session['username'] if session['username'] else "revs"
        s_name = get_student_name(s_id)
        projects = get_projects_for_id(s_id, s_username, user_type)
        print(projects)
        return render_template('view_projects.html', projects=projects, s_name=s_name, user_type=user_type)

    if user_type == 'faculty':
        f_id = session['id'] if session['id'] else "1"
        f_username = session['username'] if session['username'] else "dp"
        s_name = get_faculty_name(f_id)
        projects = get_projects_for_id(f_id, f_username, user_type)
        return render_template('view_projects.html', projects=projects, s_name=s_name, user_type=user_type)


def get_faculty_name(f_id):
    faculty_details = mongo.db.staff.find_one({'id': f_id})
    return faculty_details['name']


def get_projects_for_id(s_id, s_username="Revathi", user_type='student'):
    print("In get projects")
    research_db = mongo.db.research
    projects = []
    if user_type == 'student':
        for document in research_db.find():
            if s_id in document['students'] or s_username in document['students']:
                projects.append(document)
    elif user_type == 'faculty':
        for document in research_db.find():
            if s_id in document['staff']:
                projects.append(document)
    return projects


@app.route('/verify_report/<p_id>/<report_name>', methods=['GET', 'POST'])
def verify_report(p_id, report_name):
    s_id = session['id']
    s_name = get_faculty_name(s_id)
    print("Faculty name: ", s_name)

    user_type = get_user_type(s_id)
    print("User type: ", user_type)
    gradedReports = mongo.db.reports
    research = mongo.db.research
    project = research.find_one({"_id": ObjectId(p_id)})
    topic = project['topic']
    form = VerifyReport(request.form)
    if form.is_submitted():
        gradedReports.update_one({"projectID": p_id, "reportName": report_name}, {
            "$set": {"effort": form.effort.data, "relevance": form.relevance.data, "novelty": form.novelty.data, "date_verified":datetime.datetime.today()}})
        project['filelist'][report_name] = True
        research.update_one({"_id": ObjectId(p_id)}, {"$set": {"filelist": project['filelist']}})
        return redirect("/teacher_dashboard")

    return render_template('verify_report.html', topic=topic, form=form, s_name=s_name, user_type=user_type)


@app.route('/verify_publication/<p_id>', methods=['GET', 'POST'])
def verify_publication(p_id):
    s_id = session['id']
    s_name = get_faculty_name(s_id)
    user_type = get_user_type(s_id)
    research = mongo.db.research
    project = research.find_one({"_id": ObjectId(p_id)})
    topic = project['topic']
    doi = project['publicationDOI']
    publicationJournal = project['publicationJournal']
    publicationJournal = "ARCHIVES OF COMPUTATIONAL METHODS IN ENGINEERING"

    form = VerifyPublication(request.form)

    if form.is_submitted():
        if 'verify' in request.form:
            research.update({"topic": topic}, {"$set": {"isPublished": True}})

            impact_factor = -1
            for row in csv_file:
                if publicationJournal == row[1]:
                    impact_factor = float(row[3])
                    break

            if impact_factor == -1:
                impact_factor = 2  # Generic other journal

            students_ids = project['students']
            no_of_students = len(students_ids)
            each_student_impact_factor = impact_factor / no_of_students
            for student_id in students_ids:
                students = mongo.db.students
                students.update({"id": student_id}, {'$set': {"impactScore": each_student_impact_factor}})
            flash('Verification was successful!', 'success')
            return redirect('/teacher_dashboard')
        elif 'notVerify' in request.form:
            flash('Verification was not successful!', 'danger')
            return redirect('/teacher_dashboard')
    return render_template('verify_publication.html', form=form, topic=topic, publicationJournal=publicationJournal,
                           p_id=p_id, doi=doi, s_name=s_name, user_type=user_type)


def get_project_lists():
    my_projects = []
    topic_list = []
    filelists = []
    my_id = "171071045"

    # print("getting project lists", my_id)

    projects = mongo.db.research
    project_details = projects.find({})
    for project in project_details:
        # print("************************************", project)
        students = project["students"]
        if my_id in students:
            my_projects.append(project["_id"])
            topic_list.append(project["topic"])
            if 'filelist' in project:
                filelists.append(project["filelist"])
            else:
                filelists.append([])
            # print('No docs uploaded')
    # print(my_projects, topic_list, filelists)
    return my_projects, topic_list, filelists


@app.route('/helper_login_student')
def helper_login_student():
    session['username'] = 'Revathi'
    session['id'] = '171071045'
    return redirect('/dashboard')


@app.route('/helper_login_staff')
def helper_login_staff():
    session['username'] = 'Dr. Dhiren Patel'
    session['id'] = '1'
    return redirect('/teacher_dashboard')

@app.route('/helper_login_supervisor')
def helper_login_supervisor():
    session['username'] = 'Anna Canteen'
    session['id'] = '101'
    return redirect('/supervisor_dashboard')


# @app.route('/userlogin', methods=['POST', 'GET'])
# def userlogin():
#     if not Lib.isMobileBrowser(request):
#         return "Access to this site is only available through Mobile Phones and Tablets."
#
#     if 'username' in session:
#         print("IN Session")
#         return redirect('/home')
#
#     return render_template('pages/examples/login.html', msg = "")
#
# @app.route('/login', methods=['POST'])
# def login():
#     users = mongo.db.user
#     login_user = users.find_one({'username': request.form['username']})
#     print("{{{{{{{{{{{{{{{{{", request.form['username'], request.form.get('password'))
#     if login_user:
#         if bcrypt.hashpw(request.form.get('password').encode('utf-8'), login_user['password']) == login_user['password']:
#             session['username'] = request.form['username']
#             # print("((((((((((((((((((((((((", login_user['password'])
#             # session['type'] = "alumni"
#             return redirect('/home')
#
#     return  render_template('pages/examples/login.html', msg = "Invalid Username/Password")
#
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/register')


@app.route("/")
def home():
    return render_template('home.html')  # TODO: make generic home page

@app.route('/supervisor_dashboard', methods=['POST', 'GET'])
def supervisor_dashboard():
    s_name = get_faculty_name(session['id'])
    user_type = get_user_type(session['id'])
    return render_template('supervisor_dashboard.html', s_name=s_name, user_type=user_type)

@app.route('/view_created_jobs', methods=['POST', 'GET'])
def view_created_jobs():
    s_name = get_faculty_name(session['id'])
    user_type = get_user_type(session['id'])
    return render_template('view_created_jobs', s_name=s_name, user_type=user_type)

## THIS IS STUDENT DASHBOARD
@app.route("/dashboard", methods=['POST', 'GET'])
def dashboard():
    s_id = session['id']
    s_username = session['username']

    student = mongo.db.students.find_one({'id': s_id})

    s_name = get_student_name(s_id)
    user_type = get_user_type(s_id)
    impact_score = student['impactScore']

    all_students, student_impact_score = displayRanklist()
    wallet_address = mongo.db.wallets.find_one({'walletAddress': student['walletAddress']})
    coin_balance = wallet_address['coins']

    projects = get_projects_for_id(s_id, s_username)

    # GETTING MENTOR DETAILS FROM A LIST OF PROJECTS
    projects = get_mentor_details(projects)
    student_rank = all_students.index(s_id) + 1

    cursor = mongo.db.applicationHistory.find({'s_id': s_id})
    jobs = list(cursor)
    print(jobs)

    for i in range(len(jobs)):
        j_id = jobs[i]['j_id']
        job_details = mongo.db.jobs.find_one({'id': j_id})
        jobs[i]['job_name'] = job_details['title']
        jobs[i]['job_description'] = job_details['description']
        jobs[i]['job_duration'] = job_details['duration']
    print(jobs)

    return render_template('student_dashboard.html', title='Dashboard', s_name=s_name, project_nos=len(projects),
                           impact_score=impact_score,
                           coin_balance=coin_balance, projects=projects, total=len(all_students),
                           all_students=all_students,
                           student_impact_score=student_impact_score, student_rank=student_rank, jobs=jobs,
                           user_type=user_type)


def get_mentor_details(projects):
    # GETTING MENTOR DETAILS FROM A LIST OF PROJECTS
    for i in range(len(projects)):
        m_ids = projects[i]['staff']
        all_mentors = []
        for m_id in m_ids:
            m_name = mongo.db.staff.find_one({'id': m_id})
            # print("suck it", m_name, "projects: \n", projects[i])
            all_mentors.append(m_name['name'])
        projects[i]['mentors'] = all_mentors
    return projects


@app.route("/teacher_dashboard", methods=['POST', 'GET'])
def teacher_dashboard():
    # TODO: get teacher_id from login
    teacher_id = '1'
    s_id = session['id']
    s_name = get_faculty_name(s_id)
    user_type = get_user_type(s_id)
    research = mongo.db.research
    all_research_projects = research.find({'staff': teacher_id})
    vr_topic_list = []
    vp_topic_list = []
    p_id_vr = []
    p_id_vp = []
    report_name_vr = []

    for project in all_research_projects:

        # Any report is not verified in a certain topic
        for file in project['filelist']:
            if project['filelist'].get(file) == False:
                vr_topic_list.append(project['topic'] + ":\t" + str(file))
                p_id_vr.append(str(project['_id']))
                report_name_vr.append(file)

        # students submitted for publication but teacher needs to verify
        if project['isPublished'] == False and project['publicationDOI'] is not None and project[
            'publicationJournal'] is not None:
            vp_topic_list.append(project['topic'])
            p_id_vp.append(str(project['_id']))

    return render_template('teacher_dashboard.html', title='Dashboard', vr_topic_list=vr_topic_list, p_id_vr=p_id_vr,
                           report_name_vr=report_name_vr, total_vr=len(p_id_vr), vp_topic_list=vp_topic_list,
                           p_id_vp=p_id_vp, total_vp=len(p_id_vp), s_name=s_name, user_type=user_type)


@app.route("/ranklist", methods=['GET', 'POST'])
def ranklist():
    id = session['id']
    user_type = get_user_type(id)

    if user_type == 'student':
        s_name = get_student_name(id)
    elif user_type == 'faculty':
        s_name = get_faculty_name(id)

    all_students, student_impact_score = displayRanklist()
    student_names = []
    for student in all_students:
        student_details = mongo.db.students.find_one({'id': student})
        name = student_details['name']['fname'] + " " + student_details['name']['lname']
        student_names.append(name)

    return render_template("ranklist.html", all_students=all_students, student_impact_score=student_impact_score,
                           total=len(all_students), s_name=s_name, student_names=student_names, user_type=user_type)


def displayRanklist():
    students = mongo.db.students
    cursor = students.find({"impactScore": {"$gt": 0}})
    all_students = []
    student_score = []
    for document in cursor:
        all_students.append(document['id'])
        student_score.append(document['impactScore'])
    return all_students, student_score


# @app.route("/login", methods=['GET', 'POST'])
# def login():
#     form = LoginForm(request.form)
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#
#         #modified to use SHA512
#
#         s = 0
#         for char in (form.password.data):
#             a = ord(char)
#             s = s+a
#         now_hash = (str)((hashlib.sha512((str(s).encode('utf-8'))+((form.password.data).encode('utf-8')))).hexdigest())
#         #if user and bcrypt.check_password_hash(user.password, form.password.data):
#         if (user and (user.password==now_hash)):
#
#             login_user(user, remember=form.remember.data)
#             next_page = request.args.get('next')
#             return redirect(next_page) if next_page else redirect(url_for('dashboard'))
#
#         else:
#             print('nahin hua login')
#             flash('Login Unsuccessful. Please check email and password', 'danger')
#
#     else:
#         print('ho gaya')
#     return render_template('login.html', title='Login', form=form)
#
#
#
# @app.route("/logout")
# def logout():
#     logout_user()
#     return redirect(url_for('login'))


@app.route("/get_open_jobs", methods=["POST", "GET"])
def get_open_jobs():
    jobs_ = mongo.db.jobs
    jobs = jobs_.find({})
    s_name = get_student_name(session['id'])
    user_type = get_user_type(session['id'])
    # add condition for displaying only jobs w unfilled vacancies
    L_title = []
    L_description = []
    L_vacancies = []
    L_id = []
    for job in jobs:
        print(job["title"], job["description"], job["vacancies"])
        title, description, vacancies, id = job["title"], job["description"], job["vacancies"], job["id"]
        L_title.append(title)
        L_description.append(description)
        L_vacancies.append(vacancies)
        L_id.append(id)
    total = len(L_title)

    return render_template('get_open_jobs.html', title_list=L_title, description_list=L_description,
                           vacancies_list=L_vacancies, L_id=L_id, total=total, s_name=s_name, user_type=user_type)


# Get candidates
@app.route("/get_candidates/<job_id>", methods=["POST", "GET"])
def get_candidates(job_id):
    jobs_ = mongo.db.jobs
    job = jobs_.find_one({"id": job_id})
    job_title = job["title"]
    job_vacancies = job["vacancies"]

    candidates = job["candidates"]
    candidates_db = mongo.db.students

    L_id = []
    L_name = []
    L_description = []
    L_resume = []

    for candidate_id in candidates:
        candidate = candidates_db.find_one({"id": candidate_id})

        print(candidate["id"], candidate["name"], candidate["description"], candidate["resume"])
        id, name, description, resume = candidate["id"], candidate["name"], candidate["description"], candidate[
            "resume"]

        L_id.append(id)
        L_name.append(name)
        L_description.append(description)
        L_resume.append(resume)

        total = len(L_id)

    return render_template('get_candidates.html', id_list=L_id, name_list=L_name, description_list=L_description,
                           resume_list=L_resume, total=total, title=job_title, vacancies=job_vacancies, job_id=job_id)


# Apply for job
@app.route("/apply_for_job/<job_id>", methods=["POST", "GET"])
# by student applying for jobs
def apply_for_job(job_id):
    student_id = 171071054  # student id who has logged in
    applicationHistory = mongo.db.applicationHistory
    hasApplied = applicationHistory.find_one({'s_id': student_id, 'j_id': job_id})
    # Dont allow same student to apply multiple times for a job
    if hasApplied:
        flash("You have already applied for this job, you will be contacted shortly with the results. ", "success")
        return redirect(url_for('get_open_jobs'))
    else:
        applicationHistory.insert_one({'s_id': student_id, 'j_id': job_id, 'status': 'applied', 'grade': None})
        flash("Thank you for applying for this job, you will be contacted shortly with the results. ", "success")
        return redirect(url_for('get_open_jobs'))


# Create job
@app.route("/create_job", methods=["POST", "GET"])
def create_job():
    form = CreateJob(request.form)

    if form.is_submitted():
        print("using db")
        jobs = mongo.db.jobs
        id = str(jobs.count())
        title = request.form.get('title')
        description = request.form.get('description')
        duration = request.form.get('duration')
        vacancies = request.form.get('vacancies')
        start_date = datetime.datetime.strptime(request.form.get('start_date'), '%d %B, %Y')
        date_created = datetime.datetime.today()
        jobs.insert(
            {"id": id, "title": title, "description": description, "duration": duration, "vacancies": vacancies, "start_date":start_date, "date_created":date_created})
        return (redirect("/supervisor_dashboard"))
    return render_template('create_job.html', create_job_form=form)


# completed and tested
def allocate_job(job_id):
    applicationHistory = mongo.db.applicationHistory
    all_applicants = applicationHistory.find({'j_id': job_id}, {"s_id": 1, "_id": 0})
    all_applicants = [item['s_id'] for item in all_applicants]
    curr_job = mongo.db.jobs.find_one({"id": job_id})

    if len(list(applicationHistory.find({'status': 'selected'}))) < 0:
        selected_candidates = random.sample(all_applicants, int(curr_job["vacancies"]))
    else:
        scores = {}
        # Generate scores of students for the given job
        for applicant in all_applicants:
            all_grades = applicationHistory.find({"s_id": applicant, "status": "selected"}, {"grade": 1, "_id": 0})
            all_grades = [item['grade'] for item in all_grades]
            # If it is his first job give him an implicit rating of 9
            scores[applicant] = 9 if len(all_grades) == 0 else (sum(all_grades) / len(all_grades))

        for key in scores.keys():
            scores[key] = scores[key] * random.uniform(0.7, 1.0)
        selected_candidates = list(dict(sorted(scores.items(), key=lambda item: item[1], reverse=True)).keys())[
                              :int(curr_job["vacancies"])]

    for candidate in all_applicants:
        if candidate in selected_candidates:
            applicationHistory.update_one({'j_id': job_id, 's_id': candidate}, {'$set': {'status': 'selected'}})
        else:
            applicationHistory.update_one({'j_id': job_id, 's_id': candidate}, {'$set': {'status': 'rejected'}})

    return selected_candidates


@app.route('/grade_job/<job_id>/<candidate_id>', methods=['GET', 'POST'])
def grade_job(job_id, candidate_id):
    form = GradeJob(request.form)
    applicationHistory = mongo.db.applicationHistory
    if form.is_submitted():
        applicationHistory.update_one({"s_id": candidate_id, "j_id": job_id}, {"$set": {"grade": form.grade.data}})
        flash('The job has been graded')
        # TODO: Should the student be intimated that his job has been completed?
        return (redirect("/teacher_dashboard"))
    return render_template('grade_job.html', form=form)


if __name__ == '__main__':
    app.run(debug=True, port=1240)
