from django.shortcuts import render , HttpResponse
from products_app .models import CustomUser
# Create your views here.

def users_list(request):
    users = [i.first_name for i in CustomUser.objects.all().order_by('-id')]
    return HttpResponse(users)
