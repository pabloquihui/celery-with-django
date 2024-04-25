from django.db import models
from celery.schedules import schedule as celery_schedule
from celery.schedules import crontab 
from redbeat import RedBeatSchedulerEntry
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_project.celery import app as current_app
import redis
import logging
import os
import uuid

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('models_log.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class ScheduledTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('interval', 'Interval'),
        ('crontab', 'Crontab'),
    ]

    id = models.AutoField(primary_key=True)
    task_name = models.CharField(max_length=255)
    custom_name = models.CharField(max_length=255, default='custom')
    bulk_chat_model_id = models.CharField(max_length=255, blank=True)
    chat_id = models.CharField(max_length=255, blank=True)
    template_name = models.CharField(max_length=255, blank=True)
    template_namespace = models.CharField(max_length=255, blank=True)
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES, default='interval')
    interval_seconds = models.IntegerField(default=60)
    crontab_minute = models.CharField(max_length=64, blank=True, null=True, help_text="0-59, *, */2, 0-30/5, etc.", default="*")
    crontab_hour = models.CharField(max_length=64, blank=True, null=True, help_text="0-23, *, */2, 0-12/3, etc.", default="*")
    crontab_day_of_month = models.CharField(max_length=64, blank=True, null=True, help_text="1-31, *, */2, 1-15/3, etc.", default="*")
    crontab_month_of_year = models.CharField(max_length=64, blank=True, null=True, help_text="1-12, *, */2, 1-6/2, etc.", default="*")
    crontab_day_of_week = models.CharField(max_length=64, blank=True, null=True, help_text="0-6 (Sunday=0), *, */2, 0-3, etc.", default="*")
    redbeat_key = models.CharField(max_length=255, blank=True)
    task_id = models.UUIDField(default=uuid.uuid4, editable=False) #TODO: Cambiar esto a id
    end_datetime = models.DateTimeField(null=True, blank=True)
    max_executions = models.PositiveIntegerField(null=True, blank=True)

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
                args=[self.id, self.chat_id, self.template_name, self.template_namespace, task_id_str, self.end_datetime, self.max_executions],
            )
            entry.save()
            self.redbeat_key = entry.key  # Save the RedBeat key
            self.save()  # Save the model instance with the RedBeat key
            logger.info('Task created successfully')
        except Exception as e:
            logger.error("Failed to save task to RedBeat: %s", e)

    def delete_from_redbeat(self):
        try:
            logger.info(f'Start deleting task')
            print(self.redbeat_key)
            entry = RedBeatSchedulerEntry.from_key(key=self.redbeat_key, app=current_app)
            logger.info(f'Deleting task: {entry}')
            entry.delete()
            logger.info('Task deleted successfully')
        except Exception as e:
            logger.error("Failed to delete task %s from RedBeat: %s", self.task_name, e)
            
    def delete(self, *args, **kwargs):
        """Override the delete method to call delete_from_redbeat."""
        TaskExecution.objects.filter(scheduled_task=self).update(scheduled_task=None)
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
    scheduled_task = models.ForeignKey(ScheduledTask, on_delete=models.CASCADE, null=True)
    task_id = models.CharField(max_length=255, default="")
    execution_date = models.DateField(default=timezone.now)
    execution_time = models.TimeField(default=timezone.now)
    status = models.CharField(max_length=255, default="")
    
    # Add fields to store derived values
    task_name = models.CharField(max_length=255, default="")
    periodic_name = models.CharField(max_length=255, default="")
    execution_type = models.CharField(max_length=255, default="")
    
    chat_id = models.CharField(max_length=255, default="")
    template = models.CharField(max_length=255, default="")
    template_name_space = models.CharField(max_length=255, default="")

    def save(self, *args, **kwargs):
        if self.scheduled_task:
            # Populate derived values from ScheduledTask
            self.task_name = self.scheduled_task.custom_name
            self.periodic_name = self.scheduled_task.task_name
            self.execution_type = self.scheduled_task.task_type
        super().save(*args, **kwargs)
        
        
class ChatScheduledTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_ids = models.TextField(help_text="Enter comma-separated chat ids")
    task_name = models.CharField(max_length=255)
    custom_name = models.CharField(max_length=255, default='custom')
    template_name = models.CharField(max_length=255, blank=True)
    template_namespace = models.CharField(max_length=255, blank=True)
    task_type = models.CharField(max_length=10, choices=ScheduledTask.TASK_TYPE_CHOICES, default='interval')
    interval_seconds = models.IntegerField(default=60)
    crontab_minute = models.CharField(max_length=64, blank=True, null=True, help_text="0-59, *, */2, 0-30/5, etc.", default="*")
    crontab_hour = models.CharField(max_length=64, blank=True, null=True, help_text="0-23, *, */2, 0-12/3, etc.", default="*")
    crontab_day_of_month = models.CharField(max_length=64, blank=True, null=True, help_text="1-31, *, */2, 1-15/3, etc.", default="*")
    crontab_month_of_year = models.CharField(max_length=64, blank=True, null=True, help_text="1-12, *, */2, 1-6/2, etc.", default="*")
    crontab_day_of_week = models.CharField(max_length=64, blank=True, null=True, help_text="0-6 (Sunday=0), *, */2, 0-3, etc.", default="*")
    
    def crontab_schedule_display(self):
        parts = [
            self.crontab_minute,
            self.crontab_hour,
            self.crontab_day_of_month,
            self.crontab_month_of_year,
            self.crontab_day_of_week
        ]
        return ":".join(part for part in parts if part)
    
    def delete(self, *args, **kwargs):
        scheduled_tasks = ScheduledTask.objects.filter(bulk_chat_model_id=self.id)
        for task in scheduled_tasks:
            task.delete()
        super().delete(*args, **kwargs)
        
@receiver(post_save, sender=ChatScheduledTask)
def update_or_create_scheduled_tasks(sender, instance, created, **kwargs):
    if created:
        chat_ids = instance.chat_ids.split(',')
        i = 0
        for chat_id in chat_ids:
            ScheduledTask.objects.create(
                chat_id=chat_id.strip(),
                task_name=instance.task_name,
                custom_name=instance.custom_name + f"_{i}",  # No es necesario agregar un sufijo único
                template_name=instance.template_name,
                template_namespace=instance.template_namespace,
                task_type=instance.task_type,
                interval_seconds=instance.interval_seconds,
                crontab_minute=instance.crontab_minute,
                crontab_hour=instance.crontab_hour,
                crontab_day_of_month=instance.crontab_day_of_month,
                crontab_month_of_year=instance.crontab_month_of_year,
                crontab_day_of_week=instance.crontab_day_of_week,
                bulk_chat_model_id=instance.id
            ).save_to_redbeat()
            i += 1
    else:
        scheduled_tasks = ScheduledTask.objects.filter(bulk_chat_model_id=instance.id)
        for scheduled_task in scheduled_tasks:
            scheduled_task.task_name = instance.task_name
            scheduled_task.template_name = instance.template_name
            scheduled_task.template_namespace = instance.template_namespace
            scheduled_task.task_type = str(instance.task_type)
            scheduled_task.interval_seconds = instance.interval_seconds
            scheduled_task.crontab_minute = instance.crontab_minute
            scheduled_task.crontab_hour = instance.crontab_hour
            scheduled_task.crontab_day_of_month = instance.crontab_day_of_month
            scheduled_task.crontab_month_of_year = instance.crontab_month_of_year
            scheduled_task.crontab_day_of_week = instance.crontab_day_of_week
            scheduled_task.save_to_redbeat()

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
    
# Crear modelo con lista de chatsid, params del scheduledtask, al guardar se deberian autocrear instancias de scheduledtask
