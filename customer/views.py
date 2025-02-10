from django.shortcuts import render

# Create your views here.

# Customer Registration

def home(request):
    return render(request,'home.html')



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerRegistrationSerializer

class CustomerRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

