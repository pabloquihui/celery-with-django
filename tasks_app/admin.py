from django.contrib import admin
from .models import ScheduledTask

class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'task_path', 'interval_seconds', 'redbeat_key')
    search_fields = ('task_name', 'task_path', 'redbeat_key')
    actions = ['update_interval_action', 'delete_from_redbeat_action']

    def save_model(self, request, obj, form, change):
        """Override save_model method to call save_to_redbeat."""
        obj.save_to_redbeat()

    def update_interval_action(self, request, queryset):
        """Custom admin action to update interval for selected tasks."""
        for task in queryset:
            task.update_interval(new_interval_seconds=30)  # Update interval to 30 seconds
    update_interval_action.short_description = "Update interval for selected tasks"

    # def delete_from_redbeat_action(self, request, queryset):
    #     """Custom admin action to delete tasks from RedBeat."""
    #     for task in queryset:
    #         task.delete_from_redbeat()
    # delete_from_redbeat_action.short_description = "Delete selected tasks from RedBeat"

admin.site.register(ScheduledTask, ScheduledTaskAdmin)