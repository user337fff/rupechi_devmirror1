import os
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

def createCommand(kwargs: dict):
    return F"pytest --testit --testrunid={kwargs.get('TEST_RUN_ID')}"

@csrf_exempt
def autotestHandler(request):
    print("Статус выполнения команд", os.system(""))
    return HttpResponse("", status=200)

