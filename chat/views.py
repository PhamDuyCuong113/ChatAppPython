from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from itertools import chain
from django.http import JsonResponse, FileResponse, Http404
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
import random, os
from bson import ObjectId
from pymongo import MongoClient
import gridfs

# Models
from .models import UserProfile, Friends, Messages, GroupChat, GroupMessage, LoginOTP

# Mongo services
from .mongo_service import (
    client, db,
    get_messages, save_message, save_file_message,
    clear_chat, get_all_conversations
)

# ==========================
# 🧠 Hàm tạo danh sách bạn bè + nhóm theo thời gian tin nhắn gần nhất
# ==========================
def build_combined_list(user):
    user_profile = get_object_or_404(UserProfile, username=user.username)
    friends = UserProfile.objects.exclude(username=user_profile.username)
    groups = GroupChat.objects.filter(members=user_profile)

    for f in friends:
        last_time = None
        # 🔹 Lấy tin nhắn MongoDB mới nhất giữa 2 người
        try:
            msgs = get_messages(user_profile.username, f.username)
            if msgs:
                ts = msgs[-1].get("timestamp", "")
                if "•" in ts:
                    t, d = ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    last_time = timezone.make_aware(dt, timezone.get_current_timezone())
        except Exception as e:
            print("⚠️ Mongo error:", e)

        f.last_msg_time = last_time or timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)

    for g in groups:
        try:
            msgs = get_messages(user_profile.username, f"group_{g.id}")
            if msgs:
                ts = msgs[-1].get("timestamp", "")
                if "•" in ts:
                    t, d = ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    g.last_msg_time = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    g.last_msg_time = timezone.now()
            else:
                g.last_msg_time = timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
        except Exception as e:
            print("⚠️ Mongo group error:", e)
            g.last_msg_time = timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)

    combined = list(friends) + list(groups)
    combined.sort(key=lambda x: getattr(x, "last_msg_time", timezone.now()), reverse=True)
    return combined

# ==========================
# 🏠 Trang chủ
# ==========================
def home(request):
    return render(request, "chat/home.html")


# ==========================
# 👤 Trang cá nhân
# ==========================
@login_required
def view_profile(request, username):
    profile = get_object_or_404(UserProfile, username=username)
    return render(request, "chat/profile.html", {
        "profile": profile,
        "is_self": profile.username == request.user.username
    })


# ==========================
# 🧑‍🤝‍🧑 Danh sách bạn bè
# ==========================
def getFriendsList(user_id):
    try:
        user = UserProfile.objects.get(id=user_id)
        return [UserProfile.objects.get(id=rec.friend) for rec in user.friends_set.all()]
    except Exception as e:
        print("⚠️ Error loading friends:", e)
        return []


# ==========================
# 💬 Trang chính (Danh sách hội thoại)
# ==========================
@login_required
def index(request):
    user_profile = get_object_or_404(UserProfile, username=request.user.username)

    # 🟢 1️⃣ Lấy tất cả bạn bè (kể cả chưa nhắn)
    friends = UserProfile.objects.exclude(username=user_profile.username).all()

    # 🕓 2️⃣ Gắn preview + thời gian tin nhắn mới nhất
    for f in friends:
        last_msg_time = None
        last_msg_preview = ""

        # 🔹 SQL messages
        sql_msg = Messages.objects.filter(
            Q(sender_name=user_profile, receiver_name=f)
            | Q(sender_name=f, receiver_name=user_profile)
        ).order_by("-timestamp").first()

        if sql_msg:
            last_msg_time = timezone.localtime(sql_msg.timestamp)
            last_msg_preview = sql_msg.description or ""

        # 🔹 MongoDB messages
        try:
            msgs = get_messages(user_profile.username, f.username)
            if msgs:
                last_mongo = msgs[-1]
                mongo_text = last_mongo.get("content", "")
                mongo_ts = last_mongo.get("timestamp", "")
                if "•" in mongo_ts:
                    t, d = mongo_ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    mongo_time = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    mongo_time = timezone.now()

                # ✅ Nếu Mongo mới hơn SQL thì dùng Mongo
                if not last_msg_time or mongo_time > last_msg_time:
                    last_msg_time = mongo_time
                    last_msg_preview = mongo_text
        except Exception as e:
            print(f"⚠️ MongoDB error ({f.username}):", e)

        # ✅ Gán thuộc tính để render
        f.last_msg_preview = last_msg_preview or ""
        f.last_msg_time = last_msg_time or timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)

    # 👥 3️⃣ Lấy nhóm chat của user
    groups = GroupChat.objects.filter(members=user_profile).prefetch_related("members")

    for g in groups:
        last_msg_time = timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
        try:
            msgs = get_messages(user_profile.username, f"group_{g.id}")
            if msgs:
                last = msgs[-1]
                ts = last.get("timestamp", "")
                if "•" in ts:
                    t, d = ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    last_msg_time = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    last_msg_time = timezone.now()
        except Exception as e:
            print(f"⚠️ MongoDB group error ({g.name}):", e)

        g.last_msg_time = last_msg_time

    # 🧩 4️⃣ Gộp bạn bè + nhóm => sắp xếp theo thời gian tin nhắn gần nhất
    combined_list = list(friends) + list(groups)
    combined_list.sort(key=lambda x: getattr(x, "last_msg_time", timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)), reverse=True)

    # ✅ 5️⃣ Render ra template
    return render(request, "chat/index.html", {
        "combined_list": combined_list,
        "user_profile": user_profile,
    })



# ==========================
# 🔍 Tìm kiếm người dùng
# ==========================
@login_required
def search(request):
    curr_user = get_object_or_404(UserProfile, username=request.user.username)
    users = UserProfile.objects.exclude(username=curr_user.username)

    if request.method == "POST":
        query = request.POST.get("search", "").strip().lower()
        if query:
            users = users.filter(Q(name__icontains=query) | Q(username__icontains=query))

    friends = UserProfile.objects.filter(
        Q(sent_messages__receiver_name=curr_user)
        | Q(received_messages__sender_name=curr_user)
    ).distinct()

    return render(request, "chat/search.html", {"users": users, "friends": friends})


# ==========================
# ➕ Thêm bạn
# ==========================
@login_required
def addFriend(request, name):
    curr = get_object_or_404(UserProfile, username=request.user.username)
    friend = UserProfile.objects.filter(username__iexact=name.strip()).first()
    if friend and friend != curr:
        if not curr.friends_set.filter(friend=friend.id).exists():
            curr.friends_set.create(friend=friend.id)
            friend.friends_set.create(friend=curr.id)
    return redirect("chat:search")


# ==========================
# 💬 Chat cá nhân
# ==========================
@login_required
def chats(request, username):
    me = get_object_or_404(UserProfile, username=request.user.username)
    friend = get_object_or_404(UserProfile, username=username)

    # 🟢 1️⃣ Lấy tất cả bạn bè (kể cả chưa nhắn)
    friends = UserProfile.objects.exclude(username=me.username).all()

    # 🕓 2️⃣ Gắn thời gian và preview tin nhắn mới nhất cho mỗi bạn bè
    for f in friends:
        last_msg_time = None
        last_msg_preview = ""

        # 🔹 SQL messages
        sql_msg = Messages.objects.filter(
            Q(sender_name=me, receiver_name=f)
            | Q(sender_name=f, receiver_name=me)
        ).order_by("-timestamp").first()
        if sql_msg:
            last_msg_time = timezone.localtime(sql_msg.timestamp)
            last_msg_preview = sql_msg.description or ""

        # 🔹 MongoDB messages
        try:
            msgs = get_messages(me.username, f.username)
            if msgs:
                last_mongo = msgs[-1]
                mongo_text = last_mongo.get("content", "")
                mongo_ts = last_mongo.get("timestamp", "")
                if "•" in mongo_ts:
                    t, d = mongo_ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    mongo_time = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    mongo_time = timezone.now()

                if not last_msg_time or mongo_time > last_msg_time:
                    last_msg_time = mongo_time
                    last_msg_preview = mongo_text
        except Exception as e:
            print(f"⚠️ MongoDB error ({f.username}):", e)

        f.last_msg_preview = last_msg_preview or ""
        f.last_msg_time = last_msg_time or timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)

    # 👥 3️⃣ Lấy nhóm chat của user
    groups = GroupChat.objects.filter(members=me).prefetch_related("members")
    for g in groups:
        try:
            msgs = get_messages(me.username, f"group_{g.id}")
            if msgs:
                ts = msgs[-1].get("timestamp", "")
                if "•" in ts:
                    t, d = ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    g.last_msg_time = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    g.last_msg_time = timezone.now()
            else:
                g.last_msg_time = timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
        except Exception as e:
            print(f"⚠️ Mongo group error ({g.name}):", e)
            g.last_msg_time = timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)

    # 🧩 4️⃣ Gộp bạn bè + nhóm => sắp xếp theo thời gian mới nhất
    combined_list = list(friends) + list(groups)
    combined_list.sort(key=lambda x: getattr(x, "last_msg_time", timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)), reverse=True)

    # 💬 5️⃣ Lấy tin nhắn cá nhân từ MongoDB
    mongo_msgs = []
    try:
        mongo_msgs = get_messages(me.username, friend.username)
    except Exception as e:
        print(f"⚠️ Lỗi tải tin nhắn MongoDB: {e}")

    today = timezone.localtime().strftime("%d/%m/%Y")

    return render(request, "chat/chats.html", {
        "curr_user": me,
        "friend": friend,
        "messages": mongo_msgs,
        "combined_list": combined_list,
        "today": today,
    })



# ==========================
# 👥 Tạo nhóm mới
# ==========================
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
                continue

        return redirect("chat:group_chat", group_id=group.id)
    return redirect("chat:index")


# ==========================
# 💬 Chat nhóm
# ==========================
@login_required
def group_chat(request, group_id):
    curr_user = get_object_or_404(UserProfile, username=request.user.username)
    group = get_object_or_404(GroupChat, id=group_id)

    if curr_user not in group.members.all():
        messages.error(request, "Bạn không thuộc nhóm này.")
        return redirect("chat:index")

    # 🟢 1️⃣ Lấy tất cả bạn bè (kể cả chưa nhắn)
    friends = UserProfile.objects.exclude(username=curr_user.username).all()

    # 🕓 2️⃣ Gắn thời gian tin nhắn mới nhất cho từng bạn bè
    for f in friends:
        last_msg_time = None
        last_msg_preview = ""

        # 🔹 SQL messages
        sql_msg = Messages.objects.filter(
            Q(sender_name=curr_user, receiver_name=f)
            | Q(sender_name=f, receiver_name=curr_user)
        ).order_by("-timestamp").first()
        if sql_msg:
            last_msg_time = timezone.localtime(sql_msg.timestamp)
            last_msg_preview = sql_msg.description or ""

        # 🔹 MongoDB messages
        try:
            msgs = get_messages(curr_user.username, f.username)
            if msgs:
                last_mongo = msgs[-1]
                mongo_text = last_mongo.get("content", "")
                mongo_ts = last_mongo.get("timestamp", "")
                if "•" in mongo_ts:
                    t, d = mongo_ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    mongo_time = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    mongo_time = timezone.now()

                if not last_msg_time or mongo_time > last_msg_time:
                    last_msg_time = mongo_time
                    last_msg_preview = mongo_text
        except Exception as e:
            print(f"⚠️ MongoDB error ({f.username}):", e)

        f.last_msg_preview = last_msg_preview or ""
        f.last_msg_time = last_msg_time or timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)

    # 👥 3️⃣ Lấy tất cả nhóm của user
    groups = GroupChat.objects.filter(members=curr_user).prefetch_related("members")

    for g in groups:
        last_msg_time = timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
        try:
            msgs = get_messages(curr_user.username, f"group_{g.id}")
            if msgs:
                last = msgs[-1]
                ts = last.get("timestamp", "")
                if "•" in ts:
                    t, d = ts.split("•")
                    dt = datetime.strptime(f"{d.strip()} {t.strip()}", "%d/%m/%Y %H:%M")
                    last_msg_time = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    last_msg_time = timezone.now()
        except Exception as e:
            print(f"⚠️ MongoDB group error ({g.name}):", e)

        g.last_msg_time = last_msg_time

    # 🧩 4️⃣ Gộp bạn bè + nhóm => sắp xếp theo thời gian tin nhắn mới nhất
    combined_list = list(friends) + list(groups)
    combined_list.sort(
        key=lambda x: getattr(x, "last_msg_time", timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)),
        reverse=True
    )

    # 💬 5️⃣ Lấy tin nhắn nhóm từ MongoDB
    mongo_msgs = get_messages(curr_user.username, f"group_{group.id}") or []
    today = timezone.localtime().strftime("%d/%m/%Y")

    return render(request, "chat/group_chat.html", {
        "group": group,
        "messages": mongo_msgs,
        "curr_user": curr_user,
        "combined_list": combined_list,  # ✅ sidebar luôn hiển thị và đúng thứ tự
        "today": today,
    })



# ==========================
# ➕ Thêm / Xóa / Rời nhóm
# ==========================
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


@login_required
def view_group_members(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    return render(request, "chat/group_members.html", {
        "group": group,
        "members": group.members.all(),
    })


@login_required
def remove_member(request, group_id, username):
    group = get_object_or_404(GroupChat, id=group_id)
    member = get_object_or_404(UserProfile, username=username)
    owner = get_object_or_404(UserProfile, username=request.user.username)

    if owner != group.owner:
        messages.error(request, "Bạn không có quyền xóa thành viên này.")
    elif member == group.owner:
        messages.warning(request, "Không thể xóa chủ nhóm.")
    else:
        group.members.remove(member)
        messages.success(request, f"Đã xóa {member.username} khỏi nhóm.")

    return redirect("chat:view_group_members", group_id=group.id)


@login_required
def leave_group(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    user = get_object_or_404(UserProfile, username=request.user.username)

    if user in group.members.all():
        group.members.remove(user)
        if user == group.owner and group.members.exists():
            group.owner = group.members.first()
            group.save()
        if group.members.count() == 0:
            group.delete()
    return redirect("chat:index")


# ==========================
# 🧹 Xóa đoạn chat
# ==========================
@login_required
def clear_group_chat(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    user = get_object_or_404(UserProfile, username=request.user.username)
    if user == group.owner:
        clear_chat(user.username, f"group_{group.id}")
    return redirect("chat:group_chat", group_id=group.id)


@login_required
def clear_personal_chat(request, username):
    me = get_object_or_404(UserProfile, username=request.user.username)
    friend = get_object_or_404(UserProfile, username=username)
    Messages.objects.filter(
        Q(sender_name=me, receiver_name=friend)
        | Q(sender_name=friend, receiver_name=me)
    ).delete()
    clear_chat(me.username, friend.username)
    return redirect("chat:index")


# ==========================
# 📎 Upload / Xem file
# ==========================
fs = gridfs.GridFS(db)

@csrf_exempt
@login_required
def upload_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]
        if f.size > 25 * 1024 * 1024:
            return JsonResponse({"error": "File quá lớn (tối đa 25MB)."}, status=413)
        try:
            file_id = fs.put(
                f.read(), filename=f.name.replace(" ", "_"), contentType=f.content_type
            )
            return JsonResponse({
                "file_id": str(file_id),
                "url": f"/chat/file/{str(file_id)}/",
                "filename": f.name,
                "content_type": f.content_type,
                "is_image": f.content_type.startswith("image/"),
            })
        except Exception as e:
            print("❌ Upload failed:", e)
            return JsonResponse({"error": "Không thể lưu file."}, status=500)
    return JsonResponse({"error": "Không có file."}, status=400)


@login_required
def serve_file(request, file_id):
    try:
        grid_file = fs.get(ObjectId(file_id))
        content_type = grid_file.content_type or "application/octet-stream"
        res = FileResponse(grid_file, content_type=content_type)
        disp = "inline" if content_type.startswith("image/") or content_type == "application/pdf" else "attachment"
        res["Content-Disposition"] = f'{disp}; filename="{grid_file.filename}"'
        print(f"📦 Serving {content_type}: {grid_file.filename}")
        return res
    except Exception as e:
        print("❌ serve_file error:", e)
        raise Http404("File không tồn tại hoặc đã bị xóa.")


# ==========================
# 🔐 OTP đăng nhập
# ==========================
def send_otp(user):
    code = str(random.randint(100000, 999999))
    LoginOTP.objects.create(user=user, code=code)
    send_mail(
        subject="Mã xác thực PyChatApp",
        message=f"Mã OTP của bạn là: {code}. Có hiệu lực trong 5 phút.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            LoginOTP.objects.filter(user=user).delete()
            send_otp(user)
            request.session["pending_user"] = user.id
            return redirect("verify_otp")
        messages.error(request, "Sai tên đăng nhập hoặc mật khẩu.")
    return render(request, "registration/login.html")


def verify_otp(request):
    if request.method == "POST":
        code = request.POST.get("code")
        user_id = request.session.get("pending_user")
        if not user_id:
            messages.error(request, "Phiên đăng nhập đã hết hạn.")
            return redirect("login")

        otp = LoginOTP.objects.filter(user_id=user_id, code=code).last()
        if otp and (timezone.now() - otp.created_at).seconds < 300:
            user = otp.user
            auth_login(request, user)
            request.session.pop("pending_user", None)
            messages.success(request, "Đăng nhập thành công.")
            return redirect("chat:index")
        messages.error(request, "Mã OTP không hợp lệ hoặc đã hết hạn.")
    return render(request, "registration/verify_otp.html")


# ==========================
# 📑 Lọc tin nhắn theo loại
# ==========================
@login_required
def filter_messages(request, receiver, type):
    msgs = get_messages(request.user.username, receiver)
    results = []
    for m in msgs:
        if type == "media" and m["file"] and any(ext in m["file"]["url"].lower() for ext in [".jpg", ".png", ".jpeg"]):
            results.append({"file": m["file"]["url"]})
        elif type == "files" and m["file"] and not any(ext in m["file"]["url"].lower() for ext in [".jpg", ".png", ".jpeg"]):
            results.append({"file": m["file"]["url"]})
        elif type == "links" and m["content"] and "http" in m["content"]:
            results.append({"message": m["content"]})
    return JsonResponse({"results": results})
