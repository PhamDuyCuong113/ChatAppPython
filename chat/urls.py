from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # 🏠 Trang chính sau khi đăng nhập
    path("", views.index, name="index"),

    # 🔍 Tìm kiếm người dùng
    path("search/", views.search, name="search"),

    # ➕ Thêm bạn
    path("addfriend/<str:name>/", views.addFriend, name="addFriend"),

    # 👤 Xem profile người dùng
    path("profile/<str:username>/", views.view_profile, name="view_profile"),

    # 🏘️ Quản lý nhóm chat
    path("group/create/", views.create_group, name="create_group"),
    path("group/<int:group_id>/", views.group_chat, name="group_chat"),
    path("group/<int:group_id>/add_member/", views.add_member_to_group, name="add_member_to_group"),
    path("group/<int:group_id>/members/", views.view_group_members, name="group_members"),
    
    path("group/<int:group_id>/remove/<str:username>/", views.remove_member, name="remove_member"),
    path("group/<int:group_id>/leave/", views.leave_group, name="leave_group"),
    path("group/<int:group_id>/clear/", views.clear_group_chat, name="clear_group_chat"),

    # 🗑️ Xóa đoạn chat cá nhân (phía mình)
    path("clear/<str:username>/", views.clear_personal_chat, name="clear_personal_chat"),

    # 📎 Upload file (ảnh, tài liệu,…)
    path("upload/", views.upload_file, name="upload_file"),

    # 💬 Chat cá nhân — luôn đặt CUỐI CÙNG để không nuốt các route khác
    path("<str:username>/", views.chats, name="chat"),
    path('group/<int:group_id>/members/', views.view_group_members, name='view_group_members'),

]
