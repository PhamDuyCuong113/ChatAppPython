from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from itertools import chain
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
import os

from .models import UserProfile, Friends, Messages, GroupChat, GroupMessage


# 🏠 Trang chủ (khi chưa đăng nhập)
def home(request):
    return render(request, "chat/home.html")


# 👤 Trang xem profile người dùng
@login_required
def view_profile(request, username):
    profile = get_object_or_404(UserProfile, username=username)
    is_self = (profile.username == request.user.username)
    return render(request, "chat/profile.html", {
        "profile": profile,
        "is_self": is_self,
    })


# 📜 Lấy danh sách bạn bè của người dùng
def getFriendsList(user_id):
    try:
        user = UserProfile.objects.get(id=user_id)
        friend_records = user.friends_set.all()
        friends = []
        for record in friend_records:
            fr = UserProfile.objects.get(id=record.friend)
            friends.append(fr)
        return friends
    except Exception as e:
        print("Error loading friends:", e)
        return []


# 💬 Trang chính sau khi đăng nhập
@login_required
def index(request):
    user_profile = get_object_or_404(UserProfile, username=request.user.username)

    sent = UserProfile.objects.filter(received_messages__sender_name=user_profile)
    received = UserProfile.objects.filter(sent_messages__receiver_name=user_profile)
    friends = list(set(chain(sent, received)))

    # Gắn tin nhắn gần nhất
    for f in friends:
        f.last_msg = Messages.objects.filter(
            Q(sender_name=user_profile, receiver_name=f) |
            Q(sender_name=f, receiver_name=user_profile)
        ).order_by('-timestamp').first()

    friends.sort(
        key=lambda f: f.last_msg.timestamp if f.last_msg else None,
        reverse=True
    )

    groups = GroupChat.objects.filter(members=user_profile).prefetch_related("members")

    return render(request, "chat/index.html", {
        'friends': friends,
        'groups': groups,
        'user_profile': user_profile
    })


# 🔍 Tìm kiếm người dùng
@login_required
def search(request):
    curr_user = get_object_or_404(UserProfile, username=request.user.username)
    users = list(UserProfile.objects.exclude(username=request.user.username))

    if request.method == "POST":
        query = request.POST.get("search", "").strip().lower()
        results = [
            u for u in users
            if query in (u.name or "").lower() or query in (u.username or "").lower()
        ]
        return render(request, "chat/search.html", {'users': results})

    friends = UserProfile.objects.filter(
        Q(sent_messages__receiver_name=curr_user) |
        Q(received_messages__sender_name=curr_user)
    ).distinct()

    return render(request, "chat/search.html", {'users': users, 'friends': friends})


# ➕ Thêm bạn
@login_required
def addFriend(request, name):
    name = name.strip()
    curr_user = get_object_or_404(UserProfile, username=request.user.username)
    friend = UserProfile.objects.filter(username__iexact=name).first()

    if not friend or friend == curr_user:
        return redirect("chat:search")

    if not curr_user.friends_set.filter(friend=friend.id).exists():
        curr_user.friends_set.create(friend=friend.id)
        friend.friends_set.create(friend=curr_user.id)

    return redirect("chat:search")


# 💬 Chat cá nhân
@login_required
def chats(request, username):
    friend = get_object_or_404(UserProfile, username=username)
    me_profile = get_object_or_404(UserProfile, username=request.user.username)

    sent = UserProfile.objects.filter(received_messages__sender_name=me_profile)
    received = UserProfile.objects.filter(sent_messages__receiver_name=me_profile)
    friends = list(set(chain(sent, received)))

    for f in friends:
        f.last_msg = Messages.objects.filter(
            Q(sender_name=me_profile, receiver_name=f) |
            Q(sender_name=f, receiver_name=me_profile)
        ).order_by('-timestamp').first()

    friends.sort(
        key=lambda f: f.last_msg.timestamp if f.last_msg else None,
        reverse=True
    )

    groups = GroupChat.objects.filter(members=me_profile)

    messages = Messages.objects.filter(
        Q(sender_name=me_profile, receiver_name=friend, deleted_by_sender=False) |
        Q(sender_name=friend, receiver_name=me_profile, deleted_by_receiver=False)
    ).order_by("timestamp")

    return render(request, "chat/chats.html", {
        "friends": friends,
        "groups": groups,
        "curr_user": me_profile,
        "friend": friend,
        "curr_user_id": me_profile.id,
        "friend_id": friend.id,
        "messages": messages,
    })


# 👥 Tạo nhóm
@login_required
def create_group(request):
    if request.method == "POST":
        name = request.POST.get("group_name", "").strip()
        member_ids = request.POST.getlist("members")

        if not name:
            return redirect("chat:index")

        owner = get_object_or_404(UserProfile, username=request.user.username)
        group = GroupChat.objects.create(name=name, owner=owner)
        group.members.add(owner)

        for mid in member_ids:
            try:
                member = UserProfile.objects.get(id=mid)
                group.members.add(member)
            except UserProfile.DoesNotExist:
                pass

        return redirect("chat:group_chat", group_id=group.id)

    return redirect("chat:index")


# 💬 Chat nhóm
@login_required
def group_chat(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    curr_user = get_object_or_404(UserProfile, username=request.user.username)

    if curr_user not in group.members.all():
        messages.error(request, "Bạn không thuộc nhóm này.")
        return redirect("chat:index")

    sent = UserProfile.objects.filter(received_messages__sender_name=curr_user)
    received = UserProfile.objects.filter(sent_messages__receiver_name=curr_user)
    friends = list(set(chain(sent, received)))
    groups = GroupChat.objects.filter(members=curr_user)

    messages = GroupMessage.objects.filter(group=group).select_related("sender").order_by("timestamp")

    return render(request, "chat/group_chat.html", {
        "group": group,
        "messages": messages,
        "friends": friends,
        "groups": groups,
        "curr_user": curr_user,
    })


# ➕ Thêm thành viên vào nhóm
@login_required
def add_member_to_group(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    if request.method == "POST":
        username = request.POST.get("username")
        try:
            user = UserProfile.objects.get(username=username)
            group.members.add(user)
        except UserProfile.DoesNotExist:
            pass
    return redirect("chat:group_chat", group_id=group.id)


# 👥 Xem danh sách thành viên
@login_required
def view_group_members(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    members = group.members.all()
    return render(request, "chat/group_members.html", {
        "group": group,
        "members": members,
    })


# ❌ Xóa thành viên khỏi nhóm (chỉ chủ nhóm)
@login_required
def remove_member(request, group_id, username):
    group = get_object_or_404(GroupChat, id=group_id)
    member = get_object_or_404(UserProfile, username=username)
    owner = get_object_or_404(UserProfile, username=request.user.username)

    if owner != group.owner:
        messages.error(request, "Bạn không có quyền xóa thành viên khỏi nhóm này.")
        return redirect("chat:view_group_members", group_id=group.id)

    if member == group.owner:
        messages.warning(request, "Không thể xóa chính chủ nhóm.")
    else:
        group.members.remove(member)
        messages.success(request, f"Đã xóa {member.username} khỏi nhóm {group.name}.")

    return redirect("chat:view_group_members", group_id=group.id)


# 🚪 Rời nhóm
@login_required
def leave_group(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    curr_user = get_object_or_404(UserProfile, username=request.user.username)

    if curr_user in group.members.all():
        group.members.remove(curr_user)
        if curr_user == group.owner and group.members.exists():
            group.owner = group.members.first()
            group.save()
        if group.members.count() == 0:
            group.delete()

    return redirect("chat:index")


# 🧹 Xóa toàn bộ chat nhóm (chỉ chủ nhóm)
@login_required
def clear_group_chat(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    curr_user = get_object_or_404(UserProfile, username=request.user.username)

    if curr_user == group.owner:
        GroupMessage.objects.filter(group=group).delete()
    return redirect("chat:group_chat", group_id=group.id)


# 🗑️ Xóa đoạn chat cá nhân (phía mình)
@login_required
def clear_personal_chat(request, username):
    me = get_object_or_404(UserProfile, username=request.user.username)
    friend = get_object_or_404(UserProfile, username=username)
    Messages.objects.filter(
        Q(sender_name=me, receiver_name=friend) |
        Q(sender_name=friend, receiver_name=me)
    ).delete()
    return redirect("chat:index")


# 📎 Upload file (cho tin nhắn cá nhân / nhóm)
@csrf_exempt
@login_required
def upload_file(request):
    """
    Trả về JSON:
    {"url": "/media/uploads/files/xxx.ext", "name": "xxx.ext", "size": 12345}

    - KHÔNG trả về URL tuyệt đối để tránh lặp /media.
    - Tự tạo thư mục nếu chưa có.
    """
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        # Giới hạn dung lượng 25MB
        max_size = 25 * 1024 * 1024
        if file.size > max_size:
            return JsonResponse({"error": "File quá lớn (tối đa 25MB)."}, status=413)

        # Tạo thư mục nếu chưa có
        upload_root = os.path.join(settings.MEDIA_ROOT, "uploads", "files")
        os.makedirs(upload_root, exist_ok=True)

        # Lưu file, thay khoảng trắng bằng gạch dưới
        safe_name = file.name.replace(" ", "_")
        fs = FileSystemStorage(location=upload_root, base_url="/media/uploads/files/")
        filename = fs.save(safe_name, file)

        file_url = fs.url(filename)
        return JsonResponse({
            "url": file_url,
            "name": safe_name,
            "size": file.size
        })

    return JsonResponse({"error": "Không có file được gửi lên."}, status=400)
