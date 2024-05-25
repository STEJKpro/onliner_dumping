# Отправка писем с помощью Python.
# Базовой кодировкой на моем сервере является UTF-8, отправлять письма мы будем в cp-1251, если есть необходимость использовать другие кодировки, замените в коде на свои.
# Первым делом подкючаем нужные функции:
from email.mime.text import MIMEText  # Модуль простого текстового сообщения
from email.utils import formatdate, formataddr  # Функция кодирования даты для заголовка письма
from email.header import make_header as mkh  # Функция кодирования заголовков для письма
from email.mime.multipart import MIMEMultipart  # Модуль формирования сообщений из нескольких частей
from email.mime.base import MIMEBase  # Модуль создания частей письма
from email.encoders import encode_base64  # Модуль для кодирования присоединенных файлов
from email.mime.image import MIMEImage  # Модуль для вставки картинок в письмо
from email.utils import make_msgid as msgid  # Генерация Message_ID
from email.headerregistry import Address
import smtplib
from config import config
from jinja2 import Environment, FileSystemLoader
import logging
import imaplib
import time
import shlex
from imap_tools.imap_utf7 import utf7_decode, utf7_encode
# Загрузка шаблона из файла
file_loader = FileSystemLoader('./templates/')
env = Environment(loader=file_loader)

# Параметры
def send_email(recipient_emails:list, message_text, msg_id:str=None): 
    logging.debug(f"Отправка письма: {recipient_emails}")
    subj = '❗Неверные цены❗'
    org = config['EMAIL']['SENDER_ORG'] # фирма
    sender_name = config['EMAIL']['SENDER_NAME'] # имя отправителя
    sender_email = config['EMAIL']['SENDER_EMAIL'] # электропочта отправителя
    password = config['EMAIL']['SENDER_PASSWORD']
    email_host = config['EMAIL']['EMAIL_HOST']
    email_port = config['EMAIL']['EMAIL_PORT']
    imap_host = config['EMAIL']['EMAIL_IMAP']
    imap_port = config['EMAIL']['EMAIL_IMAP_PORT']
    imap_folder = config['EMAIL']['EMAIL_IMAP_SENT_FOLDER']
    
    # формируем письмо
    msg = MIMEMultipart('related')
    msg['Subject'] = mkh([(subj, 'UTF-8')])
    msg['Date'] = formatdate(localtime=True)
    msg['Organization'] = mkh([(org,'UTF-8')])
    msg['Message-ID'] = msgid(domain='pravim.by', idstring=msg_id)
    
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = ", ".join(recipient_emails)
    
    # Текстовая часть сообщения
    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)
    # присоединяем HTML
    to_attach = MIMEText(message_text,"html","UTF-8")
    msgAlternative.attach(to_attach)

    # Отправка письма
    with smtplib.SMTP_SSL(email_host, email_port) as server:
        server.login(sender_email, password)
        server.sendmail(to_addrs=recipient_emails, from_addr=sender_email, msg=msg.as_string())
    
    #Добавление письма в отправленные
    with imaplib.IMAP4_SSL(imap_host, imap_port) as mail:
        mail.login(sender_email, password)
        for folder in mail.list()[1]:
            print(utf7_decode(folder))
        mail.select(utf7_encode(imap_folder))
        result, _ = mail.append(utf7_encode(imap_folder), '', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        if result == 'OK':
            logging.debug(f"Message appended to Sent folder ({imap_folder})")
        else:
            logging.debug(f"Failed to append message into \"Sent\" ({imap_folder})")

def generate_message(template: str, context) -> str:
    template = env.get_template(template)
    # Рендеринг шаблона с данными
    output = template.render(context=context)
    return output