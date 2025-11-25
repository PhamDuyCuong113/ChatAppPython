<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/4d0c70ca-6231-4313-9213-b68092cd713b" />
<img width="1919" height="870" alt="image" src="https://github.com/user-attachments/assets/6c1ccf33-e385-4840-a25d-5b2da21ce8df" />


Nhớ tải zip Redis(   https://drive.google.com/file/d/1ZVLDk8j5fK5EAIHX6um0oFns0l7FUGXz/view   ) 
tải về trước sau đó giải nén và chạy file redis-server.exe trước khi chạy:

pip install -r requirements.txt

venv\Scripts\activate

python manage.py makemigrations

python manage.py migrate

daphne PyChat.asgi:application

