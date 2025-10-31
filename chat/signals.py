# chat/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Tự động tạo UserProfile khi user mới được tạo trong auth_user.
    """
    if created:
        UserProfile.objects.create(
            username=instance.username,
            name=instance.get_full_name() or instance.username,
            email=instance.email or ""
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    from .models import UserProfile
    try:
        profile = UserProfile.objects.filter(username=instance.username).first()
        if not profile:
            profile = UserProfile.objects.create(
                user=instance,
                username=instance.username,
                name=instance.get_full_name() or instance.username,
                email=instance.email or "",
            )
        else:
            profile.user = instance
            profile.name = instance.get_full_name() or instance.username
            profile.email = instance.email or ""
            profile.save()
    except Exception as e:
        print("⚠️ Lỗi khi sync UserProfile:", e)


