from django.contrib.auth import get_user_model
from celery import shared_task
from django.core.mail import send_mail
from django_celery_project import settings
from django.utils import timezone
from datetime import timedelta
import logging
import inspect
from django_celery_project.celery import app
import redis
from tasks_app.models import ScheduledTask, TaskExecution
import requests

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('reminder.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)

def execution_data(id, status):
    current_datetime = timezone.localtime()
    execution_date = current_datetime.strftime('%Y-%m-%d')
    execution_time = current_datetime.strftime('%H:%M:%S')
    task = ScheduledTask.objects.get(task_id=id)
    TaskExecution.objects.create(scheduled_task=task, task_id=id, 
                                 execution_date=execution_date, 
                                 execution_time=execution_time, 
                                 status=status)

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
def periodic_task(self, response_message=None, *args):
    # Do something periodically
    logger.info(f"Response: {response_message}")
    


@shared_task(bind=True)
def probando_task(self, response_message, task_id, *args, **kwargs):
    try:
        logger.info(f"probando ejecucion id: {task_id}")
        logger.info(f"Mensaje: {response_message}")
        task_status = "SUCCESS"
    except Exception:
        logger.error(Exception)
        task_status = "Error"
    
    execution_data(id=task_id, status=task_status)
    logger.info(f"probando ejecucion")
    
    
@shared_task(bind=True)
def template_msg_task(self, chat_id, template_name, template_namespace, localizable_params, task_id, *args, **kwargs):
    
    try:
        logger.info(f"Trying execution: {task_id}")
        url = 'http://127.0.0.1:8000/trigger-send-template-message/'
        data = {
            'chat': int(chat_id),
            'name_space': str(template_namespace),
            'element_name': str(template_name),
            'language_code': 'es_mx',
            'localizable_params': []
        }

        response = requests.post(url, data=data)
        logger.info(f"The response of sending the message is: {response.status_code}") 
        if response.status_code == 200:
            logger.info('Endpoint called sucessfully')
            task_status = "SUCCESS"
        else:
            err = response.message
            logger.error(f'Error when calling the endpoint: {err}')
            task_status = 'Error'
    except Exception:
        logger.error(f"Error trying execution: {task_id}, with exception: {Exception}")
        task_status = "Error"   
    execution_data(id=task_id, status=task_status)

# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # Define a periodic task to check for task updates
#     sender.add_periodic_task(60.0, check_task_updates.s())

# @app.task(bind=True)
# def check_task_updates(self):
#     # Retrieve task definitions from Redis
#     task_definitions = redis_conn.hgetall('tasks')

#     # Register or update Celery tasks based on task definitions
#     for task_name, task_code in task_definitions.items():
#         task_code = task_code.decode('utf-8')  # Convert bytes to string
#         task_func = app.tasks.get(task_name.decode('utf-8')) or app.task(shared=True)(eval(task_code))
#         task_func.name = task_name.decode('utf-8')  # Set task name
