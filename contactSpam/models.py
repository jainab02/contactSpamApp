from django.db import models
from django.contrib.auth.models import User

'''
used to store contact info which we store in the mobile 
setting phn number as False for spam by default
'''
class ContactDetails(models.Model):
    name = models.CharField(max_length=50, null=False)
    phone_number = models.CharField(max_length=10, null=False) 
    email = models.EmailField(max_length=50, null=True)
    spam = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} ({self.phone_number})'
    

# below mapper is used to map contact number to default user model in django
class UserContactMapper(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    contact = models.ForeignKey(ContactDetails, on_delete=models.CASCADE, null=False)

    class Meta:
        unique_together = ('user', 'contact')

    def __str__(self):
        return f'{self.user.username}, {self.contact.name}'


# making profile info 
class ProfileInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False)
    phone_number = models.CharField(max_length=10, null=False, unique=True) 
    email = models.EmailField(max_length=50, null=True)
    spam = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


# for handling the contacts spammed whether it is registered or not
class SpamNumber(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    marked_by = models.ForeignKey(User, on_delete=models.CASCADE)
    marked_at = models.DateTimeField(auto_now_add=True)