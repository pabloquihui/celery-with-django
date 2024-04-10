from django.shortcuts import render
from django.http.response import HttpResponse
from .tasks import test_func
from django.http import JsonResponse
import redis

# Create your views here.
def test(request):
    test_func.delay()
    return HttpResponse("Done")

