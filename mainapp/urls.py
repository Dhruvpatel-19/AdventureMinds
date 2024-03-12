from django.urls import path
from . import views

app_name = 'mainapp'
urlpatterns = [
    path('chat_app/', views.chat_app, name='chat_app'),
    path('', views.messenger, name='messenger'),
    path('h/', views.homepage, name='homepage'),
    path('t/', views.terms_conditions, name='terms_conditions'),
    path('home/', views.messenger, name='home'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('add_trip/', views.add_trip, name='add_trip'),
    path('trip_list/', views.trip_list, name='trip_list')
]