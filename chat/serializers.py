from rest_framework import serializers
from .models import Messages, UserProfile


class MessageSerializer(serializers.ModelSerializer):
    # Hiển thị username thay vì id
    sender_name = serializers.SlugRelatedField(
        slug_field='username',
        queryset=UserProfile.objects.all()
    )
    receiver_name = serializers.SlugRelatedField(
        slug_field='username',
        queryset=UserProfile.objects.all()
    )

    # Format lại thời gian cho dễ đọc (HH:MM)
    time = serializers.DateTimeField(source="timestamp", format="%H:%M", read_only=True)

    # Đảm bảo file có URL đầy đủ
    file = serializers.SerializerMethodField()

    class Meta:
        model = Messages
        fields = ["id", "sender_name", "receiver_name", "description", "file", "time"]

    def get_file(self, obj):
        """
        Nếu có file thì trả về URL đầy đủ (đã encode),
        nếu không có thì None.
        """
        if obj.file:
            return obj.file.url
        return None
