from django.db import models
from celery.schedules import schedule as celery_schedule
from celery.schedules import crontab 
from redbeat import RedBeatSchedulerEntry
from django.utils import timezone
from django_celery_project.celery import app as current_app
import logging

class ScheduledTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('interval', 'Interval'),
        ('crontab', 'Crontab'),
    ]

    task_name = models.CharField(max_length=255)
    custom_name = models.CharField(max_length=255, default='custom')
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES, default='interval')
    interval_seconds = models.IntegerField(default=60)
    crontab_minute = models.CharField(max_length=64, blank=True, null=True, help_text="0-59, *, */2, 0-30/5, etc.", default="*")
    crontab_hour = models.CharField(max_length=64, blank=True, null=True, help_text="0-23, *, */2, 0-12/3, etc.", default="*")
    crontab_day_of_month = models.CharField(max_length=64, blank=True, null=True, help_text="1-31, *, */2, 1-15/3, etc.", default="*")
    crontab_month_of_year = models.CharField(max_length=64, blank=True, null=True, help_text="1-12, *, */2, 1-6/2, etc.", default="*")
    crontab_day_of_week = models.CharField(max_length=64, blank=True, null=True, help_text="0-6 (Sunday=0), *, */2, 0-3, etc.", default="*")
    redbeat_key = models.CharField(max_length=255, blank=True)

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

            task_path = f"tasks_app.tasks.{self.task_name}" #TODO: Cambiar a env variables
            entry = RedBeatSchedulerEntry(
                app=current_app,
                name=self.custom_name,
                task=task_path,
                schedule=schedule,
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

