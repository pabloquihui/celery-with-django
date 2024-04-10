from django.db import models
from celery.schedules import schedule as celery_schedule
from celery.schedules import crontab 
from redbeat import RedBeatSchedulerEntry
from django.utils import timezone
from django_celery_project.celery import app as current_app
import redis
import logging
import os
import uuid

class ScheduledTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('interval', 'Interval'),
        ('crontab', 'Crontab'),
    ]

    task_name = models.CharField(max_length=255)
    custom_name = models.CharField(max_length=255, default='custom')
    response_message = models.CharField(max_length=1024, blank=True)
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES, default='interval')
    interval_seconds = models.IntegerField(default=60)
    crontab_minute = models.CharField(max_length=64, blank=True, null=True, help_text="0-59, *, */2, 0-30/5, etc.", default="*")
    crontab_hour = models.CharField(max_length=64, blank=True, null=True, help_text="0-23, *, */2, 0-12/3, etc.", default="*")
    crontab_day_of_month = models.CharField(max_length=64, blank=True, null=True, help_text="1-31, *, */2, 1-15/3, etc.", default="*")
    crontab_month_of_year = models.CharField(max_length=64, blank=True, null=True, help_text="1-12, *, */2, 1-6/2, etc.", default="*")
    crontab_day_of_week = models.CharField(max_length=64, blank=True, null=True, help_text="0-6 (Sunday=0), *, */2, 0-3, etc.", default="*")
    redbeat_key = models.CharField(max_length=255, blank=True)
    task_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def save_to_redbeat(self):
        try:
            if self.task_type == 'interval':
                schedule = celery_schedule(run_every=self.interval_seconds)
            elif self.task_type == 'crontab':
                schedule = crontab(
                    minute=self.crontab_minute,
                    hour=self.crontab_hour,
                    day_of_month=self.crontab_day_of_month,
                    month_of_year=self.crontab_month_of_year,
                    day_of_week=self.crontab_day_of_week,
                )
            else:
                raise ValueError("Invalid task type")
            task_id_str = str(self.task_id)
            task_path = f"tasks_app.tasks.{self.task_name}" #TODO: Cambiar a env variables
            entry = RedBeatSchedulerEntry(
                app=current_app,
                name=self.custom_name,
                task=task_path,
                schedule=schedule,
                args=[self.response_message, task_id_str]
            )
            entry.save()
            self.redbeat_key = entry.key  # Save the RedBeat key
            self.save()  # Save the model instance with the RedBeat key
            logging.info('Task created successfully')
        except Exception as e:
            logging.error("Failed to save task to RedBeat: %s", e)

    def update_interval(self, new_interval_seconds):
        try:
            interval = celery_schedule(run_every=new_interval_seconds)
            entry = RedBeatSchedulerEntry.from_key(key=self.redbeat_key, app=current_app)
            entry.schedule = interval
            entry.save()
            logging.info('Interval updated successfully')
        except Exception as e:
            logging.error("Failed to update interval for task %s: %s", self.task_name, e)

    def delete_from_redbeat(self):
        try:
            logging.info(f'Start deleting task')
            print(self.redbeat_key)
            entry = RedBeatSchedulerEntry.from_key(key=self.redbeat_key, app=current_app)
            logging.info(f'Deleting task: {entry}')
            entry.delete()
            logging.info('Task deleted successfully')
        except Exception as e:
            logging.error("Failed to delete task %s from RedBeat: %s", self.task_name, e)
            
    def delete(self, *args, **kwargs):
        """Override the delete method to call delete_from_redbeat."""
        self.delete_from_redbeat()
        super().delete(*args, **kwargs)
        
    def crontab_schedule_display(self):
        parts = [
            self.crontab_minute,
            self.crontab_hour,
            self.crontab_day_of_month,
            self.crontab_month_of_year,
            self.crontab_day_of_week
        ]
        return ":".join(part for part in parts if part)
    
class TaskExecution(models.Model):
    scheduled_task = models.ForeignKey(ScheduledTask, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255, default="")
    task_id = models.CharField(max_length=255, default="")
    periodic_name = models.CharField(max_length=255, default="")
    execution_type = models.CharField(max_length=255, default="")
    execution_date = models.DateField(default=timezone)
    execution_time = models.TimeField(default=timezone)
    status = models.CharField(max_length=255, default="")
    # Add more fields as needed
    
    class Meta:
        verbose_name = "Task Execution"
        verbose_name_plural = "Task Executions"



class Tasks(models.Model):
    task_name = models.CharField(max_length=255)
    task_code = models.CharField(max_length=1024, blank=True)
    inputs = models.CharField(max_length=1024, blank=True)
    
    def create_task(self):
        # Generate the task function code
        task_function_code = self.generate_task_function_code()

        # Write the task function code to tasks.py file
        self.write_task_function_to_file(task_function_code)

    def generate_task_function_code(self):
        # Define the task function code dynamically
        function_name = f"{self.task_name}_task"
        input_parameters = ', '.join([f"{elem.strip()}" for elem in self.inputs.split(',')])
        task_function_code = f"""
@shared_task(bind=True)
def {function_name}(self, {input_parameters}, *args, **kwargs):
    # Execute the task code provided
    {self.task_code}

    # Log inputs (if any)
    if self.inputs:
        logger.info(f"Task inputs: {self.inputs}")
"""
        return task_function_code

    def write_task_function_to_file(self, task_function_code):
        # Define the path to the tasks.py file
        tasks_file_path = os.path.join(os.path.dirname(__file__), 'tasks.py')
        # Write the task function code to tasks.py file
        with open(tasks_file_path, 'a') as file:
            file.write('\n\n')
            file.write(task_function_code)

    # def save_to_redis(self, task_function_code):
    #     redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)
    #     redis_conn.hset('tasks', self.task_name, task_function_code)