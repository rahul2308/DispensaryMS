# all the imports
import os
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flaskext.mysql import MySQL
import datetime
import subprocess
 
mysql = MySQL()
# create our little application :)
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'Dispensary'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
app.config.from_object(__name__)
app.config['USERNAME']=''


def get_cursor():
    return mysql.connect().cursor()

@app.teardown_appcontext
def close_db(cursor):
    """Closes the database again at the end of the request."""
    mysql.connect().close()

@app.route('/')
def show_entries():
    db = get_cursor()
    db.execute('select title, text from entries order by id desc')
    entries = db.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST']) #add
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_cursor()
    db.execute('insert into Users (Sno, RegNo, \'FirstName\', \'MiddleName\',\'LastName\', \'BloodGroup\', \'DateofBirth\', Age, Type, \'Phonenumber\', Address, email) values (?,?,?,?,?,?,?,?,?,?,?,?)',
        [request.form['Sno'], request.form['RegNo'],request.form['FirstName'],request.form['MiddleName'],request.form['LastName'],request.form['BloodGroup'],request.form['DateOfBirth'],request.form['Age'],request.form['Type'],request.form['PhoneNumber'],request.form['text'],request.form['email']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))#show_entries

# @app.route('/reg', methods=['POST']) #reg
# def add_user():
#     if not session.get('logged_in'):
#         abort(401)
#     db = get_cursor()
#     db.execute('insert into Users (Sno, RegNo, First Name, Middle Name,Last Name, Blood Group, Date of Birth, Age, Type, Phone number, Address, email) values (?, ?,?,?,?,?,?,?,?,?,?,?)',
#         [request.form['Sno'], request.form['RegNo'],request.form['FirstName'],request.form['MiddleName'],request.form['LastName'],request.form['BloodGroup'],request.form['DateOfBirth'],request.form['Age'],request.form['Type'],request.form['PhoneNumber'],request.form['text'],request.form['email']])

#     db.commit()
#     flash('New entry was successfully posted')
#     return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    db=get_cursor()
    if request.method == 'POST':
        uname=str(request.form['username'])
        pwd=str(request.form['password'])
        sql='select Count(*) from Login where UserName="%s" and Password="%s"'%(uname,pwd)
        db.execute(sql)
        data = db.fetchone()[0]
        if data ==0:
           error='Invalid username/password'
        else:
            session['logged_in'] = True
            app.config['USERNAME'] = uname
            flash('You were logged in'+app.config['USERNAME']+str(session['logged_in']))
        return redirect(url_for('show_entries'))
    return render_template('login.html', error=error) #login.html

t=0
@app.route('/inventory')
def inventory():
    db = get_cursor()
    db.execute('select * from Pharmacy order by Sno')
    entries = db.fetchall()
    return render_template('pharmventory.html',entries = entries)

@app.route('/insert',methods=['GET','POST'])
def insert():
    global t
    db=get_cursor()
    db.execute('select Count(1) from Pharmacy')
    t=db.fetchone()[0]
    flash(t)
    #t=db.fetchall[0][0]
    if request.form['btn'] == 'insert':
        sno = int(request.form['Sno'])
        name = str(request.form['Name'])
        quantity = int(request.form['qty'])
        batchno = request.form['bno']
        mfg = datetime.datetime.strptime(request.form['mfgdate'])
        exp = datetime.datetime.strptime(request.form['expdate'])
        db.execute('insert into Pharmacy values(%s,%s,%s,%s,%s,%s)'%(sno,name,quantity,batchno,mfg.isoformat(),exp.isoformat()))
        flash('New entry successfully inserted')
        return redirect(url_for('inventory'))
    else:
        for i in range( 1, t+1):
            r = str(i)
            if request.form['btn'] == 'update' + r:
                sno=request.form['Sno' + r]
                name=request.form['Name' + r]
                quantity=request.form['qty' + r]
                batchno=request.form['bno' + r]
                mfg = request.form['mfgdate' + r]
                exp = request.form['expdate' + r]
                query = 'update pharmacy set Name=?,Quantity=?,Batchno=?,ManufactureDate=?,ExpiryDate=? where Sno=?'
                db.execute(query,[name,quantity,batchno,mfg,exp,sno])
                db.commit()
                flash('Record '+sno+' updated')
                return redirect(url_for('inventory'))       
            elif request.form['btn'] == 'delete' + r:
                sno=request.form['Sno' + r]
                query='delete from pharmacy where Sno=?'
                db.execute(query,[sno])
                db.commit()
                flash('Record '+sno+' deleted')
                return redirect(url_for('inventory'))
    flash('Nothing occured'+request.form['btn'])
    return redirect(url_for('inventory'))

@app.route('/prescription')
def prescription():
    db = get_cursor()
    cur = db.execute('select * from Prescription order by RegNo asc')
    entries = cur.fetchall()
    return render_template('prescription.html',entries = entries)

@app.route('/fileprescription', methods=['GET','POST'])
def fileprescription():
    db = get_cursor()
    docno = request.form['DoctorNo']
    regno = request.form['RegNo']
    cause = request.form['Cause']
    meds = request.form['Medicine']
    qty = request.form['Quantity']
    remark = request.form['Remarks']
    db.execute('insert into Prescription values(?,?,?,?,?,?)',[docno,regno,cause,meds,qty,remark])
    db.commit()
    flash('Prescription for '+regno+' has been given')
    return redirect(url_for('prescription'))

@app.route('/employee',methods=['GET','POST'])
def employee():
    db = get_cursor()
    error=None
    chars=[chr(i) for i in xrange(ord('A'), ord('N')+1)]
    query = 'select EmpID from Login where UserName=?'
    cur = db.execute(query,[app.config['USERNAME']])
    data = cur.fetchone()
    entries =None
    if data is None:
        error = 'User details not entered properly in the database'
    else:
        cur = db.execute('select * from Users join Employee where Users.Regno=Employee.Regno and Users.Regno=?',[data[0]])
        entries = cur.fetchall()
    return render_template('employee_profile.html',entries = entries,chars=chars)

@app.route('/employeeinfo',methods=['GET','POST'])
def employeeinfo():
    return redirect(url_for('employee'))

@app.route('/student',methods=['GET','POST'])
def student():
    db = get_cursor()
    error=None
    chars=[chr(i) for i in xrange(ord('A'), ord('N')+1)]
    query = 'select EmpID from Login where UserName=?'
    cur = db.execute(query,[app.config['USERNAME']])
    data = cur.fetchone()
    entries =None
    if data is None:
        error = 'User details not entered properly in the database'
    else:
        cur = db.execute('select * from Users join Student where Users.Regno=Student.Regno and Users.Regno=?',[data[0]])
        entries = cur.fetchall()
    return render_template('student_profile.html',entries = entries,chars=chars)

@app.route('/studentinfo',methods=['GET','POST'])
def studentinfo():
    return redirect(url_for('student'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))#show_entries.html

if __name__ == '__main__':
    app.debug = True
    app.secret_key=os.urandom(24)
    app.run()
