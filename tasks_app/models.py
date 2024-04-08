from django.db import models
from celery.schedules import schedule as celery_schedule
from redbeat import RedBeatSchedulerEntry
from django_celery_project.celery import app as current_app
import logging

class ScheduledTask(models.Model):
    task_name = models.CharField(max_length=255)
    task_path = models.CharField(max_length=255)
    interval_seconds = models.IntegerField(default=60)
    redbeat_key = models.CharField(max_length=255, blank=True)  # Store the RedBeat key

    def __str__(self):
        return self.task_name

    def save_to_redbeat(self):
        try:
            interval = celery_schedule(run_every=self.interval_seconds)
            entry = RedBeatSchedulerEntry(
                app=current_app,
                name=self.task_name,
                task=self.task_path,
                schedule=interval,
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
            entry = RedBeatSchedulerEntry.from_key(key=self.redbeat_key, app=current_app)
            entry.delete()
            logging.info('Task deleted successfully')
        except Exception as e:
            logging.error("Failed to delete task %s from RedBeat: %s", self.task_name, e)
            
    def delete(self, *args, **kwargs):
        """Override the delete method to call delete_from_redbeat."""
        self.delete_from_redbeat()
        super().delete(*args, **kwargs)