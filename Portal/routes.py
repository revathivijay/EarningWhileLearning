import os
import secrets
from Portal import app
from flask import Flask, session, escape, render_template, url_for, flash, redirect, request
from werkzeug import url_encode
from Portal.forms import SubmitResearchWork, ReviewSubmission, LoginForm
import hashlib #for SHA512
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.orm import Session
import requests


@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        #modified to use SHA512

        s = 0
        for char in (form.password.data):
            a = ord(char)
            s = s+a
        now_hash = (str)((hashlib.sha512((str(s).encode('utf-8'))+((form.password.data).encode('utf-8')))).hexdigest())
        #if user and bcrypt.check_password_hash(user.password, form.password.data):
        if (user and (user.password==now_hash)):

            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))

        else:
            print('nahin hua login')
            flash('Login Unsuccessful. Please check email and password', 'danger')

    else:
        print('ho gaya')
    return render_template('login.html', title='Login', form=form)



@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/gradeSubmission")
def gradeSubmission():
    form = ReviewSubmission(request.form) 
    return render_template('grade.html', title='Grade Submission', form=form)


@app.route("/dashboard", methods= ['POST', 'GET'])
def dashboard():
    # to be added to dashboard:
    # <div class="col s6">
    #     {% for papers in studentSubmissions %}
    #         <a href = "{{ url_for('static', filename= student.ID + organizer.photo1) }}"> <img class="circle responive-img account-img" src="{{ photo1 }}"> </a>
    #     { % endfor %} 
    # </div>
    return render_template('dashboard.html', title='Dashboard')

