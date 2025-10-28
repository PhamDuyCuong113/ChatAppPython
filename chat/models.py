from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


# 🧍 Hồ sơ người dùng
class UserProfile(models.Model):
    name = models.CharField(max_length=25)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=20, unique=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.name or self.username


# 💬 Tin nhắn cá nhân (mã hóa nội dung + hỗ trợ file)
class Messages(models.Model):
    # Dữ liệu mã hóa
    _description = models.BinaryField(
        db_column='description', editable=False, null=True, blank=True
    )

    sender_name = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='sent_messages'
    )
    receiver_name = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='received_messages'
    )

    # 📎 Cho phép gửi file hoặc ảnh
    file = models.FileField(
        upload_to="uploads/files/",
        blank=True, null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'png', 'jpeg', 'gif', 'pdf', 'docx', 'zip']
        )]
    )

    time = models.TimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_receiver = models.BooleanField(default=False)

    # ==================== MÃ HÓA / GIẢI MÃ ====================
    @property
    def description(self):
        """Giải mã nội dung tin nhắn"""
        if not self._description:
            return ""
        try:
            return settings.FERNET.decrypt(self._description).decode()
        except Exception:
            try:
                return self._description.decode()
            except Exception:
                return "[Không thể giải mã tin nhắn]"

    @description.setter
    def description(self, value):
        """Mã hóa nội dung trước khi lưu"""
        if not value:
            self._description = None
            return
        text = str(value).encode()
        self._description = settings.FERNET.encrypt(text)

    def __str__(self):
        short = self.description[:30] if self.description else "(file)"
        return f"{self.sender_name.username} → {self.receiver_name.username}: {short}"

    class Meta:
        ordering = ('timestamp',)
        indexes = [
            models.Index(fields=['sender_name', 'receiver_name', 'timestamp']),
            models.Index(fields=['-timestamp']),
        ]


# 👥 Danh sách bạn bè
class Friends(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    friend = models.IntegerField()  # ID bạn bè (UserProfile.id)

    def __str__(self):
        return f"{self.user.username} ↔ {self.friend}"


# 🏘️ Nhóm chat
class GroupChat(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='owned_groups'
    )
    members = models.ManyToManyField(UserProfile, related_name='joined_groups')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Group: {self.name}"


# 💬 Tin nhắn nhóm (mã hóa nội dung + hỗ trợ file)
class GroupMessage(models.Model):
    group = models.ForeignKey(
        GroupChat, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    _content = models.BinaryField(
        db_column='content', editable=False, null=True, blank=True
    )
    file = models.FileField(
        upload_to="uploads/group_files/",
        blank=True, null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'png', 'jpeg', 'gif', 'pdf', 'docx', 'zip']
        )]
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    # ==================== MÃ HÓA / GIẢI MÃ ====================
    @property
    def content(self):
        """Giải mã nội dung tin nhắn nhóm"""
        if not self._content:
            return ""
        try:
            return settings.FERNET.decrypt(self._content).decode()
        except Exception:
            try:
                return self._content.decode()
            except Exception:
                return "[Không thể giải mã tin nhắn nhóm]"

    @content.setter
    def content(self, value):
        """Mã hóa nội dung nhóm khi gán"""
        if not value:
            self._content = None
            return
        text = str(value).encode()
        self._content = settings.FERNET.encrypt(text)

    def __str__(self):
        short = self.content[:30] if self.content else "(file)"
        return f"[{self.group.name}] {self.sender.username}: {short}"

    class Meta:
        ordering = ('timestamp',)
        indexes = [
            models.Index(fields=['group', 'timestamp']),
        ]
