#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 12:27:04 2020

@author: ben
"""

from flask import Flask, render_template, request ,redirect, send_file, flash, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dateutil.tz import gettz
import whois
import json
import pandas as pd

sess = Session()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitoring.db'
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(200), nullable=False)
    expired = db.Column(db.String(200), nullable=True)
    days_left = db.Column(db.Integer, nullable=True)
    icp = db.Column(db.String(200), nullable=True)
    completed = db.Column(db.Integer, default=0)
    registrar = db.Column(db.String(200), nullable=True)
    renew = db.Column(db.String(200), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.now(gettz("Asia/Taipei")))
    
    def __repr__(self):
        return '<Task %r>' % self.id

db.create_all()

@app.route('/', methods=['GET', 'POST'])


def index():  
    if request.method == 'POST':
        domain_content = request.form['domain'].lower()
       
        try:
            domain_expired = whois.query(domain_content).expiration_date
            domain_registrar = whois.query(domain_content).registrar
            domain_days_left = domain_expired - datetime.now()
            domain_days_left = domain_days_left.days
            ##Check Registrar
            if "NameBright" in domain_registrar or "DropCatch.com" in domain_registrar:
                domain_registrar = "NameBright"
            if "ALIBABA.COM" in domain_registrar:
                domain_registrar = "ALIBABA.COM"
        except:
            domain_expired = domain_registrar = domain_days_left = None
            domain_registrar = "NEED A MANUAL UPDATE!"
        domain_icp = request.form['icp']
        domain_renew = request.form['renew']
        domain_date_created = datetime.now(gettz("Asia/Taipei"))
        
        if checkdomain(domain_content):
            flash('The domain name already exist')
            return redirect('/')
        else:
            new_task = Todo(domain=domain_content, expired=domain_expired, days_left= domain_days_left, icp=domain_icp, renew=domain_renew, registrar=domain_registrar, date_created=domain_date_created)

            try:
                db.session.add(new_task)
                db.session.commit()
                return redirect('/')
            except:
                return 'There was an issue'
 
    else:
        tasks = Todo.query.order_by(Todo.days_left).all()
        return render_template('index.html', tasks=tasks)
   
@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
            return 'There was an issue with deleting that task'
        
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task_to_update = Todo.query.get_or_404(id)
    if request.method == 'POST':   
        task_to_update.domain = request.form['domain'].lower()
        task_to_update.icp= request.form['icp']
        task_to_update.date_created = datetime.now(gettz("Asia/Taipei"))
        task_to_update.renew = request.form['renew']
        task_to_update.registrar = request.form['registrar']
        date_expired = request.form['expired'].replace("T", " ")+":00"
        date_expired = datetime.strptime(date_expired, '%Y-%m-%d %H:%M:%S')
        task_to_update.expired = date_expired
        domain_days_left = date_expired - datetime.now()
        task_to_update.days_left = domain_days_left.days
        
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue with updating that task'
    else:
        return render_template('update.html', task=task_to_update)

@app.route('/apitest/all', methods=['GET'])
def get_apitest():
    result = db.session.execute("SELECT * FROM todo")
    # If no rows were returned (e.g., an UPDATE or DELETE), return an empty list
    if result.returns_rows == False:
        response = []

    # Convert the response to a plain list of dicts
    else:
        response = [dict(row.items()) for row in result]

    # Output the query result as JSON
    return(json.dumps(response))

@app.route('/apitest/expired', methods=['GET'])
def get_expired():
    result = db.session.execute("SELECT * FROM todo WHERE days_left < 60 ORDER BY days_left")
    # If no rows were returned (e.g., an UPDATE or DELETE), return an empty list
    if result.returns_rows == False:
        response = []

    # Convert the response to a plain list of dicts
    else:
        response = [dict(row.items()) for row in result]

    # Output the query result as JSON
    return(json.dumps(response))

@app.route('/apitest/update', methods=['GET'])
def expired_update():
    id_param =  request.args.get('id')
    if id_param is None:  
        
        #check if the is not exist in the database yet
        domain_content = request.args.get('domain').lower()
        if checkdomain(domain_content):
            return 'Domain name exist!'
        else:
            try:
                domain_expired = whois.query(domain_content).expiration_date
                domain_days_left = domain_expired - datetime.now()
                domain_days_left = domain_days_left.days
                domain_registrar = whois.query(domain_content).registrar
            except:
                domain_expired = domain_registrar = domain_days_left = None
            domain_icp = ""
            domain_renew = ""
            new_task = Todo(domain=domain_content, expired=domain_expired, days_left= domain_days_left, icp=domain_icp,  renew=domain_renew, registrar=domain_registrar)
            try:
                db.session.add(new_task)
                db.session.commit()
                return 'success'
            except:
                return 'There was an issue'
    else:
        task_to_update = Todo.query.get_or_404(id_param)
        
        #using args=1 to recheck from python_whois module
        if int(request.args.get('all')) == 1:    
            try:
                domain_expired = whois.query(request.args.get('domain')).expiration_date
            except:
                domain_expired = datetime.strptime("0001-01-1 00:00:00", '%Y-%m-%d %H:%M:%S')
                task_to_update.registrar = "NEED A MANUAL UPDATE!"
        else:
            domain_expired = task_to_update.expired
            domain_expired = datetime.strptime(domain_expired, '%Y-%m-%d %H:%M:%S')
        domain_days_left = domain_expired - datetime.now()
        task_to_update.expired = str(domain_expired)
        task_to_update.days_left = int(domain_days_left.days)  
        
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue with updating that task'

#EXPORT
@app.route('/export', methods=['GET'])
def get_branch_data_file():
    result = db.session.execute("SELECT * FROM todo")
    if result.returns_rows == False:
        response = []
    # Convert the response to a plain list of dicts
    else:
        response = [dict(row.items()) for row in result]
        
    df = pd.read_json(json.dumps(response))
    df.to_csv(r'/home/domain_monitoring/File/output.csv', index = False)
    return_file = '/home/domain_monitoring/File/output.csv'
    return send_file(return_file, as_attachment=True)
        
#FORCE UPDATE
#EMERGENCY ONLY!
@app.route('/apitest/update/force', methods=['GET'])
def force_update():
    id_param =  request.args.get('id')
    if id_param is None:
        if checkdomain(request.args.get('domain').lower()):
            new_task = forceadd(request.args.get('domain').lower())
            try:
                db.session.add(new_task)
                db.session.commit()
                return ('Force update domain')
            except:
                return 'There was an issue'
        else: return 'Domain Exist!'
    else:    
        task_to_update = Todo.query.get_or_404(id_param)
        if request.args.get('days_left') != None: task_to_update.days_left = request.args.get('days_left')
        if request.args.get('icp') != None: task_to_update.icp = request.args.get('icp')
        if request.args.get('registrar') != None: task_to_update.registrar = request.args.get('registrar')
        if request.args.get('days_left') != None: task_to_update.days_left = request.args.get('days_left')
        if request.args.get('expired') != None: task_to_update.expired = request.args.get('expired')
        try:
            db.session.commit()
            return redirect('Force Update!')
        except:
            return 'There was an issue with updating that task'
        
def forceadd(domain):
    domain_content = domain
    domain_expired = domain_days_left = domain_icp = domain_renew = domain_registrar = None
    domain_date_created = datetime.now(gettz("Asia/Taipei"))
    new_task = Todo(domain=domain_content, expired=domain_expired, days_left= domain_days_left, icp=domain_icp, renew=domain_renew, registrar=domain_registrar, date_created=domain_date_created)
    return new_task

def checkdomain(domain):
    #get all domain in the database
    tasks = Todo.query.order_by(Todo.days_left).all()
    domain_list = [val.domain for val in tasks]
    
    if domain in domain_list:
        return True
    else:
        return False
        
if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)

    app.debug = True
    app.run(host='0.0.0.0',port=80, debug=True)
