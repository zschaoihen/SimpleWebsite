from . import celery
from datetime import datetime, timedelta, date
from app.email import send_reminder_email
from app.models import User, Appointment

@celery.task
def async_send_mail():
	d = date.today() + timedelta(days=1)
	t = datetime.now().strftime("%H:%M:%S") + ' '
	appos = Appointment.query.filter_by(date=d, time=t).all()
	for appo in appos:
		user = User.query.filter_by(id=appo.user_id).first()
		send_reminder_email(user)