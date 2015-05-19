from django.shortcuts import render, redirect
from models import *
from django.contrib import messages

# Create your views here.
def user_registration(request, page=None):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        # pprint(request.POST)
        form = UserRegistrationForm1(request.POST)
        # check whether it's valid:
        if form.is_valid():
            messages.info(request, "User registration form completion success!")
            return redirect('ceph_main')
        else:
            messages.error(request, "Invalid input on user registration form")
            return redirect('ceph_main')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = UserRegistrationForm1()
        if page == '1':
            form = UserRegistrationForm1()
        elif page == '2':
            form = UserRegistrationForm2()
        return render(request, 'user_registration.html', {'user_reg_form': form})