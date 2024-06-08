from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import ContactDetailsSerializer
from rest_framework.pagination import PageNumberPagination


class ContactList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Retrieving all contacts
        contacts = ContactDetails.objects.all()
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(contacts, request)
        serializer = ContactDetailsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        name = request.data.get("name")
        phone_number = request.data.get("phone_number")
        email = request.data.get("email", None)
        # Validating required fields --basic validation
        if not name or not phone_number:
            return Response({"Error": "Both name and phone_number are required.Please enter both"}, status=status.HTTP_400_BAD_REQUEST)
        # creating new contact and its mapper
        contact = ContactDetails.objects.create(
            name=name,
            phone_number=phone_number,
            email=email
        )
        UserContactMapper.objects.create(
            user=request.user,
            contact=contact
        )
        return Response({"Message": "Contact saved."}, status=status.HTTP_201_CREATED)


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get("name")
        phone_number = request.data.get("phone_number")
        password = request.data.get("password")
        email = request.data.get("email", None)

        # basic validation
        if not name or not phone_number or not password:
            return Response({"Error": "name, phone_number, and password are required.Please enter."}, status=status.HTTP_400_BAD_REQUEST)

        # Checking if the phone number is already registered
        if ProfileInfo.objects.filter(phone_number=phone_number).exists():
            return Response({"Error": "A user with this phone_number already exists."}, status=status.HTTP_409_CONFLICT)

        # if not then Creating a new user and profile
        user = User.objects.create_user(
            username=name, password=password, email=email)
        ProfileInfo.objects.create(
            user=user, phone_number=phone_number, email=email)
        return Response({"Message": "Registered successfully!"}, status=status.HTTP_201_CREATED)


# login only application if user have token
class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # basic validation
        if not username or not password:
            return Response({"Error": "Please Enter username and password"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user:
            # if user found then creating token for that user
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"Token": token.key}, status=status.HTTP_200_OK)
        else:
            return Response({"Error": "Invalid Credentials"}, status=status.HTTP_404_NOT_FOUND)

# if you want to mark a phn no as spam then this is called


class MarkSpam(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get("phone_number")

        # Basic validation
        if not phone_number:
            return Response({"Error": "phone_number required!"}, status=status.HTTP_400_BAD_REQUEST)

        # Update existing contact and profile records if they exist
        contact_updated = ContactDetails.objects.filter(
            phone_number=phone_number).update(spam=True)
        profile_updated = ProfileInfo.objects.filter(
            phone_number=phone_number).update(spam=True)

        # Check if the phone number is already marked as spam in the SpamNumber model
        spam_number, created = SpamNumber.objects.get_or_create(
            phone_number=phone_number, defaults={'marked_by': request.user})

        if created:
            return Response({"Message": "Contact marked as spam!"}, status=status.HTTP_200_OK)
        else:
            return Response({"Message": "Phone number was already marked as spam."}, status=status.HTTP_200_OK)


# search by name
class SearchName(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        name = request.query_params.get("name")
        print(request)
        print(name)

        # basic validation
        if not name:
            return Response({"Error": "name is required!"}, status=status.HTTP_400_BAD_REQUEST)

        '''
        retrieving the data according the requirnment
        if the contains fully or partially name then it returns the result
        and appending the response accordingly
        '''
        profile_start = ProfileInfo.objects.filter(
            user__username__istartswith=name)
        profile_contain = ProfileInfo.objects.filter(
            user__username__icontains=name).exclude(user__username__istartswith=name)
        contact_start = ContactDetails.objects.filter(name__istartswith=name)
        contact_contain = ContactDetails.objects.filter(
            name__icontains=name).exclude(name__istartswith=name)

        response = []
        for profile in profile_start:
            response.append({"name": profile.user.username,
                            "phone_number": profile.phone_number, "spam": profile.spam})
        for contact in contact_start:
            response.append(
                {"name": contact.name, "phone_number": contact.phone_number, "spam": contact.spam})
        for profile in profile_contain:
            response.append({"name": profile.user.username,
                            "phone_number": profile.phone_number, "spam": profile.spam})
        for contact in contact_contain:
            response.append(
                {"name": contact.name, "phone_number": contact.phone_number, "spam": contact.spam})

        return Response(response, status=status.HTTP_200_OK)


# search by phone no
class SearchPhoneNumber(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        phone_number = request.query_params.get("phone_number")

        # basic validation
        if not phone_number:
            return Response({"Error": "Phone number required!"}, status=status.HTTP_400_BAD_REQUEST)

        # searching by phn no and returing the queryset
        profile = ProfileInfo.objects.filter(phone_number=phone_number).first()
        if profile:
            email = profile.email if UserContactMapper.objects.filter(
                user=request.user, contact__phone_number=phone_number).exists() else None
            return Response({
                "name": profile.user.username,
                "phone_number": profile.phone_number,
                "spam": profile.spam,
                "email": email
            }, status=status.HTTP_200_OK)
        else:
            contacts = ContactDetails.objects.filter(phone_number=phone_number)
            serializer = ContactDetailsSerializer(contacts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
