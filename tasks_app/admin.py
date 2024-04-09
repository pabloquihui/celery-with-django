from django.contrib import admin
from .models import ScheduledTask

class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('custom_name', 'task_name', 'task_type', 'crontab_schedule_display', 'interval_seconds', 'redbeat_key')
    search_fields = ('task_name', 'redbeat_key')
    exclude = ('redbeat_key',)
    def save_model(self, request, obj, form, change):
        """Override save_model method to call save_to_redbeat."""
        obj.save_to_redbeat()


admin.site.register(ScheduledTask, ScheduledTaskAdmin)