from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # 🔒 Validate input
        if not email or not password:
            messages.error(request, 'Please fill all fields')
            return render(request, 'auth.html')

        # 🔐 Authenticate using email as username
        try:
            user_obj = User.objects.get(username=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'auth.html')


# ---------------- REGISTER ----------------
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # 🔒 Validate input
        if not email or not password:
            messages.error(request, 'All fields are required')
            return render(request, 'auth.html')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'auth.html')

        # 🔍 Check if user exists
        if User.objects.filter(username=email).exists():
            messages.error(request, 'User already exists')
        else:
            user = User.objects.create_user(
    username=email,
    email=email,   # ✅ THIS LINE IS IMPORTANT
    password=password
)
            user.save()
            messages.success(request, 'Account created successfully')
            return redirect('login')

    return render(request, 'auth.html')


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------- DASHBOARD ----------------
@login_required
def dashboard(request):
    return render(request, 'home.html')