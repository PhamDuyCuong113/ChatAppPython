import json
import os
from datetime import datetime
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


# ========================== 1️⃣ CHAT CÁ NHÂN ==========================
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Kết nối WebSocket giữa hai người dùng"""
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.friend_username = self.scope["url_route"]["kwargs"]["username"]
        self.user_username = user.username

        # ✅ Tạo tên phòng duy nhất cho cặp người dùng
        users = sorted([self.user_username, self.friend_username])
        self.room_group_name = f"chat_{users[0]}_{users[1]}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"✅ [{self.user_username}] connected to {self.room_group_name}")

    async def disconnect(self, close_code):
        """Ngắt kết nối socket"""
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"❌ [{self.user_username}] disconnected from {self.room_group_name}")
        except Exception as e:
            print("⚠️ Disconnect error:", e)

    async def receive(self, text_data):
        """Nhận và xử lý tin nhắn cá nhân"""
        try:
            data = json.loads(text_data)
            message = (data.get("message") or "").strip()
            sender_username = data.get("sender")
            receiver_username = data.get("receiver")
            file_url = data.get("file")
            msg_id = data.get("message_id") or None

            # 🔹 Chuẩn hóa file
            if isinstance(file_url, dict):
                file_url = file_url.get("url")
            if not file_url:
                file_url = None

            # 🔹 Kiểm tra dữ liệu hợp lệ
            if not sender_username or not receiver_username:
                return
            if not message and not file_url:
                return

            # ====================== LƯU MONGODB ======================
            from .mongo_service import save_message, save_file_message

            if file_url:
                file_name = os.path.basename(file_url)
                msg_id = await sync_to_async(save_file_message)(
                    sender_username, receiver_username, file_url, file_name, 0, msg_id
                )
            else:
                msg_id = await sync_to_async(save_message)(
                    sender_username, receiver_username, message
                )

            # ====================== PHÁT REALTIME ======================
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": str(msg_id),
                    "message": message,
                    "sender": sender_username,
                    "file": file_url,
                    "time": datetime.now().strftime("%H:%M"),
                    "sender_channel": self.channel_name,
                },
            )

        except Exception as e:
            print("❌ Receive error:", e)
            await self.send(text_data=json.dumps({
                "error": f"Lỗi xử lý tin nhắn cá nhân: {e}"
            }))

    async def chat_message(self, event):
        """Phát tin nhắn realtime đến client khác"""
        # ✅ Không gửi lại cho chính sender
        if event.get("sender_channel") == self.channel_name:
            return

        # ✅ Nếu test cùng localhost (2 tab cùng user), chặn echo
        if event.get("sender") == self.scope["user"].username:
            return

        try:
            await self.send(text_data=json.dumps({
                "message_id": event.get("message_id"),
                "message": event.get("message", ""),
                "sender": event.get("sender"),
                "file": event.get("file"),
                "time": event.get("time"),
            }))
        except Exception as e:
            print("⚠️ Send error:", e)



# ========================== 2️⃣ CHAT NHÓM ==========================
class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Kết nối WebSocket nhóm"""
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.group_id = str(self.scope["url_route"]["kwargs"]["group_id"])
        self.room_group_name = f"group_{self.group_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"✅ [{user.username}] joined group {self.group_id}")

    async def disconnect(self, close_code):
        """Ngắt kết nối nhóm"""
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"❌ [{self.scope['user'].username}] left group {self.group_id}")
        except Exception as e:
            print("⚠️ Group disconnect error:", e)

    async def receive(self, text_data):
        """Nhận và xử lý tin nhắn nhóm"""
        try:
            data = json.loads(text_data)
            message = (data.get("message") or "").strip()
            sender_username = data.get("sender")
            group_id = str(data.get("group_id"))
            file_url = data.get("file")
            msg_id = data.get("message_id") or None

            # 🔹 Chuẩn hóa file
            if isinstance(file_url, dict):
                file_url = file_url.get("url")
            if not file_url:
                file_url = None

            # 🔹 Kiểm tra dữ liệu hợp lệ
            if not sender_username or not group_id:
                return
            if not message and not file_url:
                return

            # ====================== LƯU MONGODB ======================
            from .mongo_service import save_message, save_file_message
            receiver = f"group_{group_id}"

            if file_url:
                file_name = os.path.basename(file_url)
                msg_id = await sync_to_async(save_file_message)(
                    sender_username, receiver, file_url, file_name, 0, msg_id
                )
            else:
                msg_id = await sync_to_async(save_message)(
                    sender_username, receiver, message
                )

            # ====================== PHÁT REALTIME ======================
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "group_message",
                    "message_id": str(msg_id),
                    "message": message,
                    "sender": sender_username,
                    "file": file_url,
                    "time": datetime.now().strftime("%H:%M"),
                    "sender_channel": self.channel_name,
                },
            )

        except Exception as e:
            print("❌ Group receive error:", e)
            await self.send(text_data=json.dumps({
                "error": f"Lỗi xử lý tin nhắn nhóm: {e}"
            }))

    async def group_message(self, event):
        """Phát tin nhắn realtime cho mọi client trong nhóm"""
        # ✅ Không gửi lại cho chính sender
        if event.get("sender_channel") == self.channel_name:
            return

        # ✅ Nếu user sender đang mở tab thứ 2 (test cùng máy), chặn echo
        if event.get("sender") == self.scope["user"].username:
            return

        try:
            await self.send(text_data=json.dumps({
                "message_id": event.get("message_id"),
                "message": event.get("message", ""),
                "sender": event.get("sender"),
                "file": event.get("file"),
                "time": event.get("time"),
            }))
        except Exception as e:
            print("⚠️ Group send error:", e)
