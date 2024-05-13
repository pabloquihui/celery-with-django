
from django.urls import path
from django.urls.conf import include
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'msg-scheduled', ScheduledMsgViewSet)
router.register(r'chats-msg-scheduled', ChatScheduledTaskViewSet)
router.register(r'msg-execution', ChatTaskExecutionViewSet)
router.register(r'monitor-tasks', MonitorTaskViewSet)
router.register(r'monitor-execution', MonitorExecutionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
