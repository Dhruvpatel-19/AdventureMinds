from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import UserProfileForm, UserPreferencesForm, AddTripForm, TripPreferenceForm, TripSearchForm, ContactForm
from .models import *
import os
from uuid import uuid4
import django
from AdventureMinds import settings

# Create your views here.

@login_required
def user_profile(request):
    user_profile_instance, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile_instance)
        if form.is_valid():
            # Check if 'profile_photo' exists in request.FILES
            if 'profile_photo' in request.FILES:
                # Generate a unique filename
                file_name = str(uuid4()) + os.path.splitext(request.FILES['profile_photo'].name)[1]
                # Assign the unique filename to the profile_photo field
                form.instance.profile_photo.name = 'profile/' + file_name
            # Print form data before saving
            form.save()
            django.contrib.messages.success(request, 'Profile updated successfully.')
            return redirect('mainapp:profile')
    else:
        form = UserProfileForm(instance=user_profile_instance)
        user_profile_instance.user = request.user  # Set the user attribute

    return render(request, 'mainapp/profile.html', {'form': form})


@login_required
def user_preferences(request):
    user = request.user
    try:
        user_profile_instance = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        user_profile_instance = None

    if request.method == 'POST':
        form = UserPreferencesForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            preferences = UserPreferences.objects.create(user_profile=user_profile_instance)
            for category_name, choices in cleaned_data.items():
                category = PreferenceCategory.objects.get(name=category_name)
                preferences.preferences.add(*choices)

            # Assign the created preferences to the UserProfile instance
            user_profile_instance.preferences = preferences
            user_profile_instance.save()

            return redirect(reverse('mainapp:profile'))
    else:
        existing_preferences = None
        if user_profile_instance and user_profile_instance.preferences:
            existing_preferences = user_profile_instance.preferences.get_selected_preferences()

        # Pass existing preferences to the form
        form = UserPreferencesForm(instance=user_profile_instance.preferences,
                                   initial={'existing_preferences': existing_preferences})

    return render(request, 'mainapp/userPreferences.html',{'form': form, 'existing_preferences': existing_preferences})


def homepage(request):
    template = "mainapp/homepage2.html"
    context = {}
    return render(request=request, template_name=template, context=context)
    # Pass existing preferences to the template context


def terms_conditions(request):
    template = "mainapp/terms_conditions.html"
    context = {}
    return render(request=request, template_name=template, context=context)


# signup page
def user_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # if User.objects.filter(user__username=username).exists():
        #     response = HttpResponse()
        #     response.write("<p>Username already exists, choose different username</p>")
        #     return response

        names = fullname.split()
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = names[0]
        user.last_name = names[-1]
        user.save()

        userprofileobj = UserProfile.objects.create(user=user)
        userprofileobj.save()

        return redirect('mainapp:login')
    else:
        return render(request, 'registration/signup.html')


# login page
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect('mainapp:homepage')
        else:
            response = HttpResponse()
            response.write("<p>Wrong credentials</p>")
            return response
    else:
        return render(request, 'registration/login.html')


# logout page
def user_logout(request):
    logout(request)
    return redirect('mainapp:login')


def message_button(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        second_person = get_object_or_404(User, id=user_id)
        second_person_obj = UserProfile.objects.get(user=second_person)
        first_person = request.user
        first_person_obj = UserProfile.objects.get(user=first_person)

        if first_person_obj != second_person_obj:
            chat, created = UserChat.objects.get_or_create(
                first_person=first_person_obj,
                second_person=second_person_obj,
            )
            return redirect('mainapp:messages')
        else:
            return redirect('mainapp:messages')


def getusers(request):
    users = UserProfile.objects.all().values('username', 'id')
    return JsonResponse(list(users), safe=False)


@login_required
def messages(request):

    user_profile = UserProfile.objects.get(user=request.user)
    last_active_userchat_id = request.session.get('last_active_userchat_id')
    userchats = UserChat.objects.filter(Q(first_person=user_profile) | Q(second_person=user_profile) | Q(group__members=user_profile)).prefetch_related('chatmessage_userchat').order_by('timestamp').distinct()

    context = {
        'userchats': userchats,
        'last_active_userchat_id': last_active_userchat_id
    }

    return render(request, 'mainapp/messages.html', context)

@login_required
def set_last_active_userchat_id(request):
    userchat_id = request.POST.get('userchat_id')
    request.session['last_active_userchat_id'] = userchat_id
    return JsonResponse({'status': 'success'})


def create_group(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        selected_users = request.POST.getlist('selected_users')

        group = ChatGroup.objects.create(name=group_name)
        first_person = request.user
        user_profile = UserProfile.objects.get(user=first_person)
        group.members.add(user_profile)

        if len(selected_users) < 1:
            return HttpResponse("<h1>Please select At least one user.</h1>")

        for selected_user in selected_users:
            profile = UserProfile.objects.get(user=selected_user)
            group.members.add(profile)

        chat, created = UserChat.objects.get_or_create(
            first_person=user_profile,
            group_id=group.id,
        )

        django.contrib.messages.success(request, 'Group created successfully.')

        return redirect('mainapp:messages')
    else:
        user_profile = UserProfile.objects.get(user=request.user)
        userchats = UserChat.objects.filter(Q(first_person=user_profile) | Q(second_person=user_profile) | Q(group__members=user_profile)).prefetch_related('chatmessage_userchat').order_by('timestamp')
        context = {
            'userchats': userchats
        }
        return render(request, 'mainapp/create_group.html', context)


@require_POST
@csrf_exempt
def mark_messages_as_read(request):
    userchat_id = request.POST.get('userchat_id')
    user_id = request.POST.get('user_id')
    if not userchat_id:
        return JsonResponse({'error': 'UserChat ID is required'}, status=400)
    try:
        userchat = UserChat.objects.get(id=userchat_id)
        ChatMessage.objects.filter(userchat=userchat).exclude(user__id=user_id).update(read=True)
        return JsonResponse({'success': True})
    except UserChat.DoesNotExist:
        return JsonResponse({'error': 'UserChat not found'}, status=404)


@login_required(login_url='mainapp:login')
def add_trip(request):
    if request.method == 'POST':
        trip_form = AddTripForm(request.POST, request.FILES, user=request.user)
        preference_form = TripPreferenceForm(request.POST)
        if trip_form.is_valid() and preference_form.is_valid():

            # Save the trip data
            trip = trip_form.save(commit=False)
            trip.uploader = request.user

            # Create a new TripPreference object
            trip_preference = TripPreference.objects.create()

            # Retrieve the selected preference choices from the form data
            selected_preferences = [int(choice_id) for field in preference_form.cleaned_data.values() for choice_id in
                                    field]

            # Get the PreferenceChoice objects corresponding to the selected preference choices
            preferences = PreferenceChoice.objects.filter(id__in=selected_preferences)

            # Associate preferences with the TripPreference object
            trip_preference.preferences.set(preferences)

            # Link the TripPreference object to the Trip object
            trip.preferences = trip_preference

            # Save the Trip object
            trip.save()

            # Save uploaded photos
            for photo in request.FILES.getlist('photos'):
                trip_photo = TripPhoto(trip=trip, photo=photo)
                trip_photo.save()

            # Debugging: Print data
            print("Trip data:", trip.__dict__)
            print("Trip preferences:", trip.preferences.__dict__)
            print("Uploaded photos:", [photo.__dict__ for photo in trip.photos.all()])

            return redirect('mainapp:homepage')  # Redirect to some success URL
    else:
        trip_form = AddTripForm(user=request.user)
        preference_form = TripPreferenceForm()
    return render(request, 'mainapp/add_trip.html', {'trip_form': trip_form, 'preference_form': preference_form})


@login_required
def trip_list(request):
    if request.user.is_authenticated:
        # For logged-in users
        user_profile = get_object_or_404(UserProfile, user=request.user)
        if not user_profile.preferences:
            return redirect('mainapp:user_preferences')
        user_preferences = user_profile.preferences.preferences.prefetch_related('preferences')

        trips = Trip.objects.all()

        # Apply search filter if query parameter exists
        query = request.GET.get('query')
        if query:
            trips = trips.filter(Q(place__name__icontains=query) | Q(place__address__icontains=query))

        # Filter "My Trips" if requested
        if 'my_trips' in request.GET:
            trips = trips.filter(uploader=request.user)

        # Sorting
        sort_by = request.GET.get('sort_by')
        if sort_by == 'recommendation':
            # Calculate similarity scores for each trip
            similarity_scores = {}
            for trip in trips:
                # Get the TripPreference associated with the trip
                trip_preference = trip.preferences
                if trip_preference:
                    similarity_score = calculate_similarity(user_preferences,
                                                            trip_preference.preferences.prefetch_related('preferences'))
                    similarity_scores[trip.id] = similarity_score

            # Sort trips based on similarity scores
            trips = sorted(trips, key=lambda x: similarity_scores.get(x.id, 0), reverse=True)
        elif sort_by == 'alphabetical':
            trips = trips.order_by('place__name')

        # Retrieve saved searches from cookies
        saved_searches = request.COOKIES.get('saved_searches', '').split('|')

        # Handle search query
        if query:
            # Save the search query to cookies
            saved_searches.append(query)
            saved_searches = list(set(saved_searches))[-5:]  # Limit to last 5 unique queries
            response = render(request, 'mainapp/homepage2.html', {'trips': trips, 'saved_searches': saved_searches, 'query': query})
            response.set_cookie('saved_searches', '|'.join(saved_searches), max_age=3600*24*7)  # Save for 1 week

            return response

        return render(request, 'mainapp/homepage2.html', {'trips': trips, 'saved_searches': saved_searches})
    else:
        # For guest users
        trips = Trip.objects.all()
        return render(request, 'mainapp/guest_trip_list.html', {'trips': trips})



def calculate_similarity(user_preferences, trip_preferences):
    user_pref_set = set(user_preferences.values_list('id', flat=True))
    trip_pref_set = set(trip_preferences.values_list('id', flat=True))
    #jaccard similarity
    intersection = len(user_pref_set.intersection(trip_pref_set))
    union = len(user_pref_set.union(trip_pref_set))

    if union == 0:
        return 0.0

    jaccard_similarity = intersection / union

    return jaccard_similarity





def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    join_request = None
    if request.user.is_authenticated:
        join_request = JoinRequest.objects.filter(trip=trip, user=request.user).first()
    return render(request, 'mainapp/trip_detail.html', {'trip': trip, 'join_request': join_request})


def view_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    return render(request, 'mainapp/view_profile.html', {'profile_user': profile_user})



@login_required
def join_trip(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    user = request.user

    # Check if the user has already requested to join the trip
    existing_request = JoinRequest.objects.filter(trip=trip, user=user).exists()
    if existing_request:
        django.contrib.messages.warning(request, "You have already requested to join this trip.")
        return redirect('mainapp:trip_detail', trip_id=trip_id)

    # Create a new join request
    join_request = JoinRequest.objects.create(trip=trip, user=user, status='pending')
    django.contrib.messages.success(request, "Your join request has been submitted successfully.")
    return redirect('mainapp:trip_detail', trip_id=trip_id)


def accept_join_request(request, trip_id, request_id):
    trip = get_object_or_404(Trip, id=trip_id)
    join_request = get_object_or_404(JoinRequest, id=request_id)

    # Add the user to the trip participants
    trip.participants.add(join_request.user)

    # Delete the join request
    join_request.delete()

    return redirect('mainapp:trip_detail', trip_id=trip_id)


def decline_join_request(request, trip_id, request_id):
    join_request = get_object_or_404(JoinRequest, id=request_id)

    # Delete the join request
    join_request.delete()

    return redirect('mainapp:trip_detail', trip_id=trip_id)


def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'mainapp/contact_us.html')
    else:
        form = ContactForm()
        return render(request, 'mainapp/contact_us.html', {'form': form})
