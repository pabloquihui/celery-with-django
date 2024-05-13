from rest_framework import viewsets
from .models import *
from .serializers import *

class ScheduledMsgViewSet(viewsets.ModelViewSet):
    queryset = ScheduledTask.objects.all()
    serializer_class = ScheduledMsgSerializer

class ChatScheduledTaskViewSet(viewsets.ModelViewSet):
    queryset = ChatScheduledTask.objects.all()
    serializer_class = ChatScheduledTaskSerializer
    
class ChatTaskExecutionViewSet(viewsets.ModelViewSet):
    queryset = TaskExecution.objects.all()
    serializer_class = ChatTaskExecutionSerializer

class MonitorExecutionViewSet(viewsets.ModelViewSet):
    queryset = MonitorExecution.objects.all()
    serializer_class = MonitorExecutionSerializer   

class MonitorTaskViewSet(viewsets.ModelViewSet):
    queryset = MonitoringTask.objects.all()
    serializer_class = MonitorTaskSerializer      
 

