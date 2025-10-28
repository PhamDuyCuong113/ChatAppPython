from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth import login
from chat.models import UserProfile


def SignUp(request):
    """
    Sign up view
    """
    message = []
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            email = form.validate_email()
            username = form.validate_username()
            password = form.validate_password()

            if not email:
                message.append("Email already registered!")
            elif not password:
                message.append("Passwords don't match!")
            elif not username:
                message.append("Username already registered!")
            else:
                user = form.save()  # create user in auth_user
                profile = UserProfile.objects.create(
                    user=user,
                    name=name,
                    email=email,
                    username=username
                )
                login(request, user)
                return redirect("/chat/")
    else:
        form = SignUpForm()

    return render(
        request,
        "registration/signup.html",
        {"form": form, "heading": "Sign Up", "message": message}
    )
