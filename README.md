Nhớ tải zip Redis(   https://drive.google.com/file/d/1ZVLDk8j5fK5EAIHX6um0oFns0l7FUGXz/view   ) 
tải về trước sau đó giải nén và chạy file redis-server.exe trước khi chạy:

pip install -r requirements.txt

venv\Scripts\activate

python manage.py makemigrations

python manage.py migrate

daphne PyChat.asgi:application

