from celery import shared_task
from django.utils import timezone
import logging
import requests

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('reminder.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def execution_data(id, status, chat_id, template_name, name_space):
    from tasks_app.models import ScheduledTask, TaskExecution
    logger.info(f'chat_id:{chat_id}')
    current_datetime = timezone.localtime()
    execution_date = current_datetime.strftime('%Y-%m-%d')
    execution_time = current_datetime.strftime('%H:%M:%S')
    task = ScheduledTask.objects.get(task_id=id)
    # Increment the execution count
    task.execution_count += 1
    task.save()  # Save the updated execution count back to the database
    TaskExecution.objects.create(scheduled_task=task, 
                                 task_id=id, 
                                 execution_date=execution_date, 
                                 execution_time=execution_time,
                                 chat_id=chat_id,
                                 template=template_name,
                                 template_name_space=name_space,
                                 status=status)
    
def execution_monitor(id, status):
    from tasks_app.models import MonitoringTask, MonitorExecution
    logger.info(f'Monitor task execution id:{id}')
    current_datetime = timezone.localtime()
    execution_date = current_datetime.strftime('%Y-%m-%d')
    execution_time = current_datetime.strftime('%H:%M:%S')
    task = MonitoringTask.objects.get(task_id=id)
    # Increment the execution count
    task.execution_count += 1
    task.save()  # Save the updated execution count back to the database
    MonitorExecution.objects.create(monitor_task=task, 
                                 task_id=id, 
                                 execution_date=execution_date, 
                                 execution_time=execution_time,
                                 status=status)


def check_time(end_datetime):
    current_datetime = timezone.localtime()
    logger.info(f"date now: {current_datetime}")
    if current_datetime >= end_datetime:
        logger.info(f"task out of date: {end_datetime} vs {current_datetime}")
        return True
    else:
        logger.info(f"task in date: {end_datetime} vs {current_datetime}")
        return False

def checkMaxRuns(max_runs, current_runs):
    logger.info(f"max runs: {max_runs}")
    logger.info(f"Current runs: {current_runs}")
    if current_runs >= max_runs:
        logger.info(f"Run out of range: Task executed {current_runs}/{max_runs} already.")
        return True
    else:
        logger.info(f"Run in range: Task executed {current_runs}/{max_runs}.")
        return False
    
def checkOnSchedule(task, end_date, max_runs):
    current_runs = task.execution_count
    if end_date and check_time(end_date):
        try:
            task.on_schedule = False
            task.save()
            task.delete_from_redbeat()
            logger.info('Task deleted from redbeat due to OOD')
            return
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
    if max_runs and checkMaxRuns(max_runs, current_runs):
        try:
            task.on_schedule = False
            # task.execution_count = 0 #TODO: Queremos esto? O mantener el historico de cuantas ejecuciones lleva?
            task.save()
            task.delete_from_redbeat()
            logger.info('Task deleted from redbeat due to maximum executions')
            return
        except Exception as e:
            logger.error(f"Error deleting task: {e}")

@shared_task(bind=True)
def template_msg(self, instance_id, chat_id, template_name, template_namespace, task_id, end_datetime, max_runs, *args, **kwargs):
    try:
        logger.info(f"Task with ID: {task_id}")
        from tasks_app.models import ScheduledTask
        scheduledTask = ScheduledTask.objects.get(task_id=task_id)
        checkOnSchedule(task=scheduledTask, end_date=end_datetime, max_runs=max_runs)
        logger.info(f"Trying execution with task id: {task_id}")
        url = 'http://127.0.0.1:8000/trigger-send-template-message/'
        data = {
            'chat': int(chat_id),
            'name_space': str(template_namespace),
            'element_name': str(template_name),
            'language_code': 'es_mx',
        }

        response = requests.post(url, data=data)
        logger.info(f"The response of sending the message is: {response}")

        # Check the status code of the response
        if response.status_code == 200:
            logger.info('Endpoint called successfully')
            task_status = "SUCCESS"
        else:
            err = response.text  # Access the response content for error message
            logger.error(f'Error when calling the endpoint: {err}')
            task_status = 'Error'
    except Exception as e:
        logger.error(f"Error trying execution: {task_id}, with exception: {e}")
        task_status = "Error"
    logger.info(f"The chat id is: {chat_id}")
    execution_data(id=task_id, status=task_status, chat_id=chat_id, template_name=template_name, name_space=template_namespace)
    
    

@shared_task(bind=True)
def monitoring_service(self, instance_id, task_id, end_datetime, max_runs, *args, **kwargs):
    try:
        logger.info(f"Monitoring task with ID: {task_id}")
        from tasks_app.models import MonitoringTask
        monitoringTask = MonitoringTask.objects.get(task_id=task_id)
        checkOnSchedule(task=monitoringTask, end_date=end_datetime, max_runs=max_runs)
        url = 'http://127.0.0.1:8000/check-service/'
        data = {'testing':'True'}

        response = requests.post(url=url, data=data)
        logger.info(f"The response of checking the service is: {response}")

        # Check the status code of the response
        if response.status_code == 200:
            logger.info('Endpoint called successfully')
            task_status = "SUCCESS"
        else:
            err = response.text  # Access the response content for error message
            logger.error(f'Error when calling the endpoint: {err}')
            task_status = 'Error'
    except Exception as e:
        logger.error(f"Error trying execution: {task_id}, with exception: {e}")
        task_status = "Error"
    execution_monitor(id=task_id, status=task_status)
    