from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Review, Rating

# class SignupForm(UserCreationForm):
#     class Meta:
#         model = User
#         # fields = ['username', 'password1', 'password2']
#         fields = '__all__'

class SignupForm(forms.Form):
    firstname = forms.CharField()
    lastname = forms.CharField()
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()

# class SignupForm(UserCreationForm):
#     username = forms.CharField(max_length=20)
#     email = forms.EmailField()
#     phone_no = forms.CharField(max_length = 20)
#     first_name = forms.CharField(max_length = 20)
#     last_name = forms.CharField(max_length = 20)
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'phone_no', 'password1', 'password2']


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review', 'place', 'user']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'place', 'user']

# class BlogForm(forms.ModelForm):
#     class Meta:
#         model = Post
#         fields = ['title', 'body', 'place']