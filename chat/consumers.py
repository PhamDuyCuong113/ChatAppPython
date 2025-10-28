import json
from datetime import datetime
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


# ========================== 1️⃣ CHAT CÁ NHÂN ==========================
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Kết nối WebSocket giữa 2 người dùng"""
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.friend_username = self.scope["url_route"]["kwargs"]["username"]
        self.user_username = user.username

        # Tạo tên nhóm cố định, tránh trùng
        users = sorted([self.user_username, self.friend_username])
        self.room_group_name = f"chat_{users[0]}_{users[1]}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"✅ [{self.user_username}] connected to {self.room_group_name}")

    async def disconnect(self, close_code):
        """Ngắt kết nối"""
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"❌ [{self.user_username}] disconnected from {self.room_group_name}")
        except Exception as e:
            print("⚠️ Disconnect error:", e)

    async def receive(self, text_data):
        """Nhận và xử lý tin nhắn cá nhân (văn bản + file)"""
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            sender_username = data.get("sender")
            receiver_username = data.get("receiver")
            file_url = data.get("file")

            if not message and not file_url:
                return

            from .models import UserProfile, Messages

            sender = await sync_to_async(UserProfile.objects.get)(username=sender_username)
            receiver = await sync_to_async(UserProfile.objects.get)(username=receiver_username)

            # ✅ Lưu tin nhắn vào DB
            msg = Messages(sender_name=sender, receiver_name=receiver)
            if message:
                msg.description = message  # setter tự mã hóa
            if file_url:
                # chỉ lưu tên file (không lưu full URL)
                msg.file.name = file_url.replace("/media/", "").lstrip("/")
            await sync_to_async(msg.save)()

            # ✅ Gửi tin nhắn tới nhóm (cả 2 người)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": sender_username,
                    "time": datetime.now().strftime("%H:%M"),
                    "file": file_url,
                },
            )

        except Exception as e:
            print("❌ Receive error:", e)

    async def chat_message(self, event):
        """Trả dữ liệu về client"""
        await self.send(text_data=json.dumps({
            "message": event.get("message", ""),
            "sender": event["sender"],
            "time": event["time"],
            "file": event.get("file"),
        }))



# ========================== 2️⃣ CHAT NHÓM ==========================
class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Kết nối WebSocket nhóm"""
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.room_group_name = f"group_{self.group_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"✅ [{user.username}] joined group {self.group_id}")

    async def disconnect(self, close_code):
        """Ngắt kết nối khỏi nhóm"""
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"❌ [{self.scope['user'].username}] left group {self.group_id}")
        except Exception as e:
            print("⚠️ Group disconnect error:", e)

    async def receive(self, text_data):
        """Nhận và xử lý tin nhắn nhóm (văn bản + file)"""
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            sender_username = data.get("sender")
            group_id = data.get("group_id")
            file_url = data.get("file")

            if not message and not file_url:
                return

            from .models import UserProfile, GroupChat, GroupMessage

            sender = await sync_to_async(UserProfile.objects.get)(username=sender_username)
            group = await sync_to_async(GroupChat.objects.get)(id=group_id)

            msg = GroupMessage(group=group, sender=sender)
            if message:
                msg.content = message
            if file_url:
                msg.file.name = file_url.replace("/media/", "").lstrip("/")
            await sync_to_async(msg.save)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "group_message",
                    "message": message,
                    "sender": sender_username,
                    "time": datetime.now().strftime("%H:%M"),
                    "file": file_url,
                },
            )

        except Exception as e:
            print("❌ Group receive error:", e)

    async def group_message(self, event):
        """Trả dữ liệu về client"""
        await self.send(text_data=json.dumps({
            "message": event.get("message", ""),
            "sender": event["sender"],
            "time": event["time"],
            "file": event.get("file"),
        }))
