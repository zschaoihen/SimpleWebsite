from datetime import datetime, tzinfo
import time
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AppointmentForm, \
    ResetPasswordRequestForm, ResetPasswordForm, CreateDogForm, EditDogForm, RescheduleApp, \
    EditServiceForm, CreateServiceForm
from app.models import User, Appointment, Dog, Service
from app.email import send_password_reset_email

timeslot = ["09:00:00 ", "10:30:00 ", "12:00:00 ", "13:30:00 ", "15:00:00 "]

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.is_administrator:
        return redirect(url_for('administrator', username=current_user.username))
    form = AppointmentForm(datetime.now().date(), current_user.id)
    if form.validate_on_submit():
        appointment = Appointment(address=current_user.address, 
            date=datetime.strptime(form.date.data, "%Y-%m-%d").date(),
            time=timeslot[int(form.time.data)], 
            comment=form.comment.data, applicant=current_user, 
            fordog=Dog.query.filter_by(id=form.dog.data,user_id=current_user.id).first(),
            type=Service.query.filter_by(id=form.service.data).first())
        db.session.add(appointment)
        db.session.commit()
        flash('Your appointment is already submitted!')
        return redirect(url_for('user', username=current_user.username))
    return render_template('index.html', title='Home', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('user', username=current_user.username)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    appointments = user.appointments.filter_by(complete=False).order_by(Appointment.create_time.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=appointments.next_num) \
        if appointments.has_next else None
    prev_url = url_for('user', username=user.username, page=appointments.prev_num) \
        if appointments.has_prev else None
    return render_template('user.html', user=user, appointments=appointments.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.address = form.address.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.address.data = current_user.address
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/doglist', methods=['GET', 'POST'])
@login_required
def doglist():
    page = request.args.get('page', 1, type=int)
    dogs = Dog.query.filter_by(user_id=current_user.id).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('doglist', page=dogs.next_num) \
        if dogs.has_next else None
    prev_url = url_for('doglist', page=dogs.prev_num) \
        if dogs.has_prev else None
    return render_template('doglist.html',dogs=dogs.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/add_dog', methods=['GET', 'POST'])
@login_required
def add_dog():
    form = CreateDogForm()
    if form.validate_on_submit():
        dog = Dog(name=form.name.data, dog_type=form.dog_type.data, \
            age=form.age.data, length=form.length.data, gender=form.gender.data, \
            comment=form.comment.data, owner=current_user)
        db.session.add(dog)
        db.session.commit()
        flash('This dog is been added to your list.')
        return redirect(url_for('doglist'))
    return render_template('add_dog.html', title='Add a new Dog',
                           form=form)

@app.route('/edit_dog/<dogname>', methods=['GET', 'POST'])
@login_required
def edit_dog(dogname):
    form = EditDogForm()
    current_dog = Dog.query.filter(Dog.user_id == current_user.id, Dog.name ==dogname).first()
    if form.validate_on_submit():
        current_dog.name = form.name.data
        current_dog.dog_type = form.dog_type.data
        current_dog.age = form.age.data
        current_dog.length = form.length.data
        current_dog.gender = form.gender.data
        current_dog.comment = form.comment.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('doglist'))
    elif request.method == 'GET':
        form.name.data = current_dog.name 
        form.dog_type.data = current_dog.dog_type
        form.age.data = current_dog.age 
        form.length.data = current_dog.length 
        form.gender.data = current_dog.gender 
        form.comment.data = current_dog.comment
    return render_template('edit_dog.html', dogname=dogname, title='Edit Dog\'s Profile',
                           form=form)

@app.route('/administrator/<username>')
@login_required
def administrator(username):
    if not current_user.is_administrator:
        flash('Permission Denied')
        return redirect(url_for('user', username=current_user.username))
    page = request.args.get('page', 1, type=int)
    appointments = Appointment.query.filter_by(complete=False).order_by(Appointment.date.asc(), Appointment.time.asc()).paginate(
        page, 10, False)
    next_url = url_for('administrator', username=username, page=appointments.next_num) \
        if appointments.has_next else None
    prev_url = url_for('administrator', username=username, page=appointments.prev_num) \
        if appointments.has_prev else None
    return render_template('administrator.html', administrator=current_user, appointments=appointments.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/reschedule/<appointment>', methods=['GET', 'POST'])
@login_required
def reschedule(appointment):
    appo = Appointment.query.filter_by(id=appointment).first()
    form = RescheduleApp(appo.date, appo.user_id)
    if form.validate_on_submit():
        appo.date = datetime.strptime(form.date.data, "%Y-%m-%d").date()
        appo.time = timeslot[int(form.time.data)+1]
        db.session.commit()
        flash('Your changes have been saved!')
        if not current_user.is_administrator:
            return redirect(url_for('user', username=current_user.username))
        else:
            return redirect(url_for('administrator', username=current_user.username))
    elif request.method == 'GET':
        form.date.data = appo.date
        form.time.data = appo.time
    return render_template('reschedule.html', title='Reschedule Appointment',
                           form=form)


@app.route('/complete/<appointment>')
@login_required
def complete(appointment):
    appo = Appointment.query.filter_by(id=appointment).first()
    appo.complete = True
    db.session.commit()
    flash('This appointment has been marked as completed.')
    return redirect(url_for('administrator', username=current_user.username))

@app.route('/delete/<appointment>')
@login_required
def delete(appointment):
    appo = Appointment.query.filter_by(id=appointment).first()
    db.session.delete(appo)
    db.session.commit()
    flash('This appointment has already been deleted.')
    return redirect(url_for('administrator', username=current_user.username))

@app.route('/servicelist', methods=['GET', 'POST'])
@login_required
def servicelist():
    page = request.args.get('page', 1, type=int)
    services = Service.query.filter_by(expired=False).order_by(Service.price.desc()).paginate(
        page, 10, False)
    next_url = url_for('servicelist', page=services.next_num) \
        if services.has_next else None
    prev_url = url_for('servicelist', page=services.prev_num) \
        if services.has_prev else None
    return render_template('servicelist.html',services=services.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/add_service', methods=['GET', 'POST'])
@login_required
def add_service():
    form = CreateServiceForm()
    if form.validate_on_submit():
        service = Service(name=form.name.data, price=form.price.data)
        db.session.add(service)
        db.session.commit()
        flash('This service is online now!')
        return redirect(url_for('servicelist'))
    return render_template('add_service.html', title='Add a new Service',
                           form=form)

@app.route('/edit_service/<servicename>', methods=['GET', 'POST'])
@login_required
def edit_service(servicename):
    form = EditServiceForm()
    current_service = Service.query.filter_by(name=servicename).first()
    if form.validate_on_submit():
        current_service.name = form.name.data
        current_service.price = form.price.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('servicelist'))
    elif request.method == 'GET':
        form.name.data = current_service.name  
        form.price.data = current_service.price
    return render_template('edit_service.html', servicename=servicename, title='Edit Service',
                           form=form)

@app.route('/expire_service/<service_id>')
@login_required
def expire_service(service_id):
    service = Service.query.filter_by(id=service_id).first()
    db.session.delete(service)
    db.session.commit()
    flash('This service is offline now.')
    return redirect(url_for('servicelist'))


@app.route('/userlist', methods=['GET', 'POST'])
@login_required
def userlist():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.id.asc()).paginate(
        page, 10, False)
    next_url = url_for('userlist', page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('userlist', page=users.prev_num) \
        if users.has_prev else None
    return render_template('userlist.html',users=users.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/deleteuser/<user_id>', methods=['GET', 'POST'])
@login_required
def deleteuser(user_id):
    user = User.query.filter_by(id=user_id).first()
    appos = Appointment.query.filter_by(user_id=user_id).all()
    for appo in appos:
        db.session.delete(appo)
    db.session.delete(user)
    db.session.commit()
    flash('This user has already been deleted.')
    return redirect(url_for('userlist'))

@app.route('/set_permission/<user_id>:<administrator>', methods=['GET', 'POST'])
@login_required
def set_permission(user_id, administrator):
    if administrator == 'True':
        administrator = True
    else:
        administrator = False
    user = User.query.filter_by(id=user_id).first()
    user.administrator = administrator
    db.session.commit()
    if administrator:
        flash('This user has already been set as a administrator.')
    else:
        flash('This user has already been set as a normal user.')
    return redirect(url_for('userlist'))

