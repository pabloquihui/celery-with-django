from rest_framework import serializers
from .models import *

class ScheduledMsgSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledTask
        fields = '__all__'
class ChatScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatScheduledTask
        fields = '__all__'
        
class ChatTaskExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskExecution
        fields = '__all__'
        
class MonitorExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorExecution
        fields = '__all__'
        
class MonitorTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringTask
        fields = '__all__'