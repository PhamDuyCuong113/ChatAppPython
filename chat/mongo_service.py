from pymongo import MongoClient
from django.conf import settings
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone as dj_timezone
from bson import ObjectId
import bson
import os


# ==========================
# 🔗 Kết nối MongoDB Atlas
# ==========================
try:
    mongo_url = getattr(settings, "MONGO_URL", None)
    if not mongo_url:
        raise Exception("Missing MONGO_URL in settings.py")

    client = MongoClient(
        mongo_url,
        connectTimeoutMS=10000,
        serverSelectionTimeoutMS=10000,
        socketTimeoutMS=20000,
        retryWrites=True
    )

    db = client["PyChatApp"]
    messages_col = db["messages"]

    messages_col.create_index(
        [("sender", 1), ("receiver", 1), ("timestamp", 1)],
        background=True
    )

    print("✅ Connected to MongoDB Atlas successfully.")
except Exception as e:
    print("⚠️ MongoDB connection or index setup failed:", e)
    client = db = messages_col = None


# ==========================
# 🕒 Múi giờ Việt Nam
# ==========================
VN_TZ = dj_timezone.get_current_timezone()


# ==========================
# 💬 Lưu tin nhắn văn bản
# ==========================
def save_message(sender: str, receiver: str, text: str):
    """Lưu tin nhắn văn bản (async-safe)."""
    if not messages_col or not text.strip():
        return None
    try:
        message_id = ObjectId()
        doc = {
            "_id": message_id,
            "sender": sender,
            "receiver": receiver,
            "type": "text",
            "content": text.strip(),
            "file": None,
            "timestamp": datetime.now(dt_timezone.utc),
        }
        messages_col.insert_one(doc)
        print(f"💾 [TEXT] {sender} → {receiver}: {text[:60]}")
        return str(message_id)
    except Exception as e:
        print("❌ Error saving text message:", e)
        return None


# ==========================
# 🖼️ Lưu tin nhắn có file đính kèm
# ==========================
def save_file_message(sender: str, receiver: str, file_url: str,
                      file_name: str, file_size: int = 0, message_id: str = None):
    """
    Lưu tin nhắn có file (ảnh, pdf, docx...).
    Nếu message_id đã tồn tại thì bỏ qua (tránh trùng).
    Hỗ trợ UUID (randomUUID từ frontend).
    """
    if not messages_col or not file_url:
        return None
    try:
        # ✅ Chuyển message_id thành ObjectId an toàn
        try:
            msg_id = ObjectId(message_id)
        except (bson.errors.InvalidId, TypeError):
            msg_id = ObjectId()  # tạo mới nếu UUID hoặc None

        # Nếu message đã tồn tại -> bỏ qua
        if message_id and messages_col.find_one({"_id": msg_id}):
            print(f"⚠️ Skip duplicate file message {message_id}")
            return str(msg_id)

        ext = os.path.splitext(file_name)[1].lower()
        doc = {
            "_id": msg_id,
            "sender": sender,
            "receiver": receiver,
            "type": "file",
            "content": None,
            "file": {
                "url": file_url,
                "name": file_name,
                "type": ext,
                "size": file_size or 0,
            },
            "timestamp": datetime.now(dt_timezone.utc),
        }

        messages_col.insert_one(doc)
        print(f"📎 [FILE] {sender} → {receiver}: {file_name}")
        return str(msg_id)
    except Exception as e:
        print("❌ Error saving file message:", e)
        return None


# ==========================
# 🕰️ Định dạng thời gian hiển thị
# ==========================
def format_time(ts):
    """Đưa datetime UTC về dạng 'HH:MM • DD/MM/YYYY' theo giờ VN."""
    if not ts:
        return ""
    try:
        if not isinstance(ts, datetime):
            try:
                ts = ts.as_datetime()
            except Exception:
                return str(ts)

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt_timezone.utc)
        local_time = ts.astimezone(VN_TZ)
        return local_time.strftime("%H:%M • %d/%m/%Y")
    except Exception as e:
        print("⚠️ Error formatting time:", e)
        return str(ts)


# ==========================
# 📜 Lấy tin nhắn (cá nhân hoặc nhóm)
# ==========================
def get_messages(sender: str, receiver: str):
    """Lấy toàn bộ tin nhắn giữa hai user hoặc trong nhóm."""
    if not messages_col:
        return []

    try:
        # Chat nhóm
        if receiver.startswith("group_"):
            cursor = list(messages_col.find({"receiver": receiver}).sort("timestamp", 1))
        else:
            cursor = list(messages_col.find({
                "$or": [
                    {"sender": sender, "receiver": receiver},
                    {"sender": receiver, "receiver": sender}
                ]
            }).sort("timestamp", 1))

        messages = []
        for m in cursor:
            ts_formatted = format_time(m.get("timestamp"))
            messages.append({
                "id": str(m.get("_id")),
                "sender": m.get("sender"),
                "receiver": m.get("receiver"),
                "type": m.get("type", "text"),
                "content": m.get("content", ""),
                "file": m.get("file"),
                "timestamp": ts_formatted,
                "date_only": ts_formatted.split("•")[-1].strip() if "•" in ts_formatted else "",
            })
        return messages

    except Exception as e:
        print("❌ Error loading messages:", e)
        return []


# ==========================
# 🧹 Xóa toàn bộ đoạn chat
# ==========================
def clear_chat(sender: str, receiver: str):
    """Xóa toàn bộ tin nhắn giữa 2 user hoặc 1 nhóm."""
    if not messages_col:
        return
    try:
        if receiver.startswith("group_"):
            result = messages_col.delete_many({"receiver": receiver})
            print(f"🗑️ Cleared group chat {receiver} ({result.deleted_count} msgs)")
        else:
            result = messages_col.delete_many({
                "$or": [
                    {"sender": sender, "receiver": receiver},
                    {"sender": receiver, "receiver": sender}
                ]
            })
            print(f"🗑️ Cleared chat {sender} ↔ {receiver} ({result.deleted_count} msgs)")
    except Exception as e:
        print("❌ Error clearing chat:", e)


# ==========================
# 🔍 Lấy danh sách hội thoại
# ==========================
def get_all_conversations(username: str):
    """Lấy danh sách tất cả user hoặc nhóm mà user từng nhắn tin."""
    if not messages_col:
        return []
    try:
        users = set()
        for doc in messages_col.find(
            {"$or": [{"sender": username}, {"receiver": username}]},
            {"sender": 1, "receiver": 1}
        ):
            users.add(doc.get("sender"))
            users.add(doc.get("receiver"))
        users.discard(username)
        return list(users)
    except Exception as e:
        print("❌ Error loading conversations:", e)
        return []

def delete_message_from_mongo(message_id):
    try:
        result = messages_col.delete_one({"_id": ObjectId(message_id)})
        print(f"🗑 Deleted message: {message_id} ({result.deleted_count} docs)")
    except Exception as e:
        print("⚠️ Delete failed:", e)