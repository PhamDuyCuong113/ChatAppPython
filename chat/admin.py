from django.contrib import admin
from .models import UserProfile, Friends, Messages, GroupChat, GroupMessage


# ==================== USER PROFILE ====================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "name", "email")
    search_fields = ("username", "name", "email")


# ==================== FRIENDS ====================
@admin.register(Friends)
class FriendsAdmin(admin.ModelAdmin):
    list_display = ("user", "friend")
    search_fields = ("user__username", "friend")


# ==================== PRIVATE MESSAGES ====================
@admin.register(Messages)
class MessagesAdmin(admin.ModelAdmin):
    list_display = (
        "sender_name",
        "receiver_name",
        "preview_description",
        "encrypted_preview",
        "timestamp",
    )
    search_fields = (
        "sender_name__username",
        "receiver_name__username",
        "_description",
    )
    ordering = ("-timestamp",)
    readonly_fields = ("encrypted_preview",)

    def preview_description(self, obj):
        """Hiển thị tin nhắn đã giải mã"""
        return obj.description[:50] if obj.description else ""
    preview_description.short_description = "Decrypted Message"

    def encrypted_preview(self, obj):
        """Hiển thị dữ liệu mã hóa thật từ DB"""
        if obj._description:
            return obj._description[:60]  # Cắt ngắn cho gọn
        return "(empty)"
    encrypted_preview.short_description = "Encrypted Data (Binary)"


# ==================== GROUP MESSAGES ====================
@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "sender",
        "preview_content",
        "encrypted_preview",
        "timestamp",
    )
    list_filter = ("group", "sender")
    search_fields = ("_content", "sender__username", "group__name")
    ordering = ("-timestamp",)
    readonly_fields = ("encrypted_preview",)

    def preview_content(self, obj):
        """Hiển thị tin nhắn nhóm (đã giải mã)"""
        return obj.content[:50] if obj.content else ""
    preview_content.short_description = "Decrypted Message"

    def encrypted_preview(self, obj):
        """Hiển thị nội dung mã hóa thực tế"""
        if obj._content:
            return obj._content[:60]
        return "(empty)"
    encrypted_preview.short_description = "Encrypted Data (Binary)"


# ==================== GROUP CHAT ====================
class GroupMessageInline(admin.TabularInline):
    model = GroupMessage
    extra = 0
    fields = ("sender", "preview_content", "timestamp")
    readonly_fields = ("preview_content", "timestamp")

    def preview_content(self, obj):
        return obj.content[:50] if obj.content else ""
    preview_content.short_description = "Message (Decrypted)"


@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    inlines = [GroupMessageInline]
