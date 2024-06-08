from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

class ContactDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactDetails
        fields = '__all__'
