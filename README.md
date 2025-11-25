<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/4d0c70ca-6231-4313-9213-b68092cd713b" />
Xác thực OTP
<img width="1919" height="870" alt="image" src="https://github.com/user-attachments/assets/6c1ccf33-e385-4840-a25d-5b2da21ce8df" />
Chat nhóm
<img width="1918" height="871" alt="image" src="https://github.com/user-attachments/assets/4fee9f1c-08aa-46f3-9f96-d0ddffa451a2" />
Chat cá nhân
<img width="1919" height="875" alt="image" src="https://github.com/user-attachments/assets/ce9bf5ae-9d16-4e51-8440-be36a0a46fbc" />
<img width="1919" height="875" alt="image" src="https://github.com/user-attachments/assets/0011efd6-259b-490c-9f5b-9f691312072d" />
<img width="1919" height="873" alt="image" src="https://github.com/user-attachments/assets/4c213cbe-cc8a-4edc-bb4c-fc2ffcec104a" />
<img width="1919" height="872" alt="image" src="https://github.com/user-attachments/assets/7e520919-6742-4da7-95e1-8027d111ee9e" />
<img width="1915" height="874" alt="image" src="https://github.com/user-attachments/assets/7056dd56-9b2c-43a6-bc18-db0e276003f6" />
<img width="1919" height="870" alt="image" src="https://github.com/user-attachments/assets/5523f4dd-cbb3-404b-8858-e5d2516df79c" />
<img width="1917" height="875" alt="image" src="https://github.com/user-attachments/assets/287e24e9-27d4-413a-b494-f9a94062e552" />


Nhớ tải zip Redis(   https://drive.google.com/file/d/1ZVLDk8j5fK5EAIHX6um0oFns0l7FUGXz/view   ) 
tải về trước sau đó giải nén và chạy file redis-server.exe trước khi chạy:

pip install -r requirements.txt

venv\Scripts\activate

python manage.py makemigrations

python manage.py migrate

daphne PyChat.asgi:application

