# chat/serializers.py
from rest_framework import serializers
from .models import Messages, UserProfile


class MessageSerializer(serializers.ModelSerializer):
    """
    Dùng cho API hoặc các view REST.
    Hiển thị username thay vì id, format thời gian dạng HH:MM.
    """
    sender_name = serializers.SlugRelatedField(
        slug_field='username',
        queryset=UserProfile.objects.all()
    )
    receiver_name = serializers.SlugRelatedField(
        slug_field='username',
        queryset=UserProfile.objects.all()
    )

    # format giờ cho dễ đọc
    time = serializers.DateTimeField(source="timestamp", format="%H:%M", read_only=True)

    # serializer cho file (đảm bảo có URL tuyệt đối)
    file = serializers.SerializerMethodField()

    class Meta:
        model = Messages
        fields = ["id", "sender_name", "receiver_name", "description", "file", "time"]

    def get_file(self, obj):
        """
        Nếu có file thì trả về URL đầy đủ (hoặc None nếu trống).
        """
        try:
            if obj.file:
                request = self.context.get('request')
                url = obj.file.url
                # Nếu có request, trả URL tuyệt đối
                if request:
                    return request.build_absolute_uri(url)
                return url
            return None
        except Exception:
            return None
