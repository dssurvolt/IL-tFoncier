import smtplib
from email.mime.text import MIMEText

msg = MIMEText('Test contents')
msg['Subject'] = 'Test Subject'
msg['From'] = 'upworktechrh@gmail.com'
msg['To'] = 'upworktechrh@gmail.com'

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('upworktechrh@gmail.com', 'tddrqqiiufrtyafb')
    server.send_message(msg)
    server.quit()
    print("SUCCESS")
except Exception as e:
    print(f"FAILURE: {e}")
