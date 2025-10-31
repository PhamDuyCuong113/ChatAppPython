from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from .forms import SignUpForm
from chat.models import UserProfile, LoginOTP
import random
from django.utils import timezone


def SignUp(request):
    """
    Trang đăng ký tài khoản mới + gửi OTP xác thực qua email
    """
    message = []
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            password1 = form.cleaned_data.get("password1")
            password2 = form.cleaned_data.get("password2")

            # Kiểm tra trùng username / email
            if User.objects.filter(username=username).exists():
                message.append("⚠️ Username đã tồn tại!")
            elif User.objects.filter(email=email).exists():
                message.append("⚠️ Email đã được đăng ký!")
            elif password1 != password2:
                message.append("⚠️ Mật khẩu nhập lại không khớp!")
            else:
                # Tạo tài khoản mới
                user = form.save()

                # Tạo hoặc lấy profile (tránh lỗi trùng UNIQUE)
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "name": name,
                        "email": email,
                        "username": username,
                    },
                )

                # Tạo mã OTP ngẫu nhiên
                otp_code = random.randint(100000, 999999)
                LoginOTP.objects.create(user=user, code=otp_code, created_at=timezone.now())

                # Gửi email chứa OTP
                try:
                    send_mail(
                        subject="Mã xác thực đăng nhập ChatApp",
                        message=f"Mã OTP của bạn là: {otp_code}\nMã có hiệu lực trong 5 phút.",
                        from_email="phamduycuong2005241@gmail.com",
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception as e:
                    messages.error(request, f"Lỗi khi gửi email OTP: {str(e)}")
                    return redirect("/signup/")

                # Lưu user chờ xác thực
                request.session["pending_user"] = user.id
                messages.success(request, "🎉 Đăng ký thành công! Mã OTP đã được gửi tới email của bạn.")
                return redirect("/verify-otp/")
    else:
        form = SignUpForm()

    return render(
        request,
        "registration/signup.html",
        {"form": form, "heading": "Sign Up", "message": message},
    )
