from django.contrib.auth import get_user_model

from celery import shared_task
from django.core.mail import send_mail
from django_celery_project import settings
from django.utils import timezone
from datetime import timedelta
import logging

@shared_task(bind=True)
def send_mail_func(self):
    users = get_user_model().objects.all()
    #timezone.localtime(users.date_time) + timedelta(days=2)
    for user in users:
        mail_subject = "Hi! Celery Testing"
        message = "Klaybot Message"
        to_email = user.email
        send_mail(
            subject = mail_subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[to_email],
            fail_silently=True,
        )
    return "Done"

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('reminder.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

@shared_task(bind=True)
def test_func(self):
    #operations
    for i in range(10):
        print(i)
    return "Done"

@shared_task
def log_reminder(message):
    logger.info(message)

@shared_task(bind=True)
def periodic_task(self, *args):
    # Do something periodically
    logger.info("This is a periodic task.")