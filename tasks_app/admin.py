from django.contrib import admin
from .models import *
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('custom_name', 'task_id', 'bulk_chat_model_id', 'execution_count', 'task_name', 'task_type', 'crontab_schedule_display', 'interval_seconds', 'template_name', 'template_namespace', 'chat_id', 'redbeat_key')
    search_fields = ('task_name', 'template_name', 'template_namespace', 'chat_id', 'redbeat_key')
    exclude = ('redbeat_key',)
    readonly_fields = ('execution_count',)
    
    def save_model(self, request, obj, form, change):
        """Override save_model method to call save_to_redbeat."""
        obj.save_to_redbeat()
        
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
        
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

class ChatScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('chat_ids', 'id', 'task_name', 'custom_name', 'template_name', 'task_type', 'crontab_schedule_display', 'interval_seconds')  # Campos que se mostrarán en la lista
    search_fields = ('chat_ids', 'task_name', 'custom_name', 'template_name', 'task_type')  # Campos por los que se puede buscar
    list_filter = ('chat_ids', 'task_name', 'template_name', 'task_type') 
    fields = ['chat_ids', 'task_name', 'custom_name', 'template_name', 'template_namespace', 'task_type', 'interval_seconds', 'crontab_minute', 'crontab_hour', 'crontab_day_of_month', 'crontab_month_of_year', 'crontab_day_of_week']
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.append('custom_name')
        return readonly_fields
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
admin.site.register(ScheduledTask, ScheduledTaskAdmin)
admin.site.register(Tasks, TasksAdmin)
admin.site.register(TaskExecution, TaskExecutionAdmin)
admin.site.register(ChatScheduledTask, ChatScheduledTaskAdmin)