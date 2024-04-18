from django.contrib import admin
from .models import ScheduledTask, Tasks, TaskExecution

class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('custom_name', 'task_name', 'task_type', 'crontab_schedule_display', 'interval_seconds', 'template_name', 'template_namespace', 'chat_id', 'redbeat_key')
    search_fields = ('task_name', 'template_name', 'template_namespace', 'chat_id', 'redbeat_key')
    exclude = ('redbeat_key',)
    def save_model(self, request, obj, form, change):
        """Override save_model method to call save_to_redbeat."""
        obj.save_to_redbeat()
        
class TasksAdmin(admin.ModelAdmin):
    list_display = ('task_name',)
    search_fields = ('task_name',)
    def save_model(self, request, obj, form, change):
        """Override save_model method to call save_to_redbeat."""
        obj.create_task()

class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'task_id', 'periodic_name', 'chat_id', 'template', 'template_name_space', 'execution_type', 'execution_date', 'execution_time', 'status']
    readonly_fields = ['task_name', 'task_id', 'periodic_name', 'execution_type', 'execution_date', 'execution_time', 'status']
    list_filter = ('task_id', 'task_name', 'periodic_name', 'execution_date', 'execution_time', 'status', 'execution_type')

admin.site.register(ScheduledTask, ScheduledTaskAdmin)
admin.site.register(Tasks, TasksAdmin)
admin.site.register(TaskExecution, TaskExecutionAdmin)