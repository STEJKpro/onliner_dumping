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
import configparser
from jinja2 import Environment, FileSystemLoader

# Загрузка шаблона из файла
file_loader = FileSystemLoader('./templates/')
env = Environment(loader=file_loader)

#Загрузка конфига
config = configparser.ConfigParser()
config.read('config.ini', 'UTF-8')
# Параметры
def send_email(recipient_emails:list, message_text, msg_id:str=None): 
    subj = '❗Неверные цены❗'
    org = config['EMAIL']['SENDER_ORG'] # фирма
    sender_name = config['EMAIL']['SENDER_NAME'] # имя отправителя
    sender_email = config['EMAIL']['SENDER_EMAIL'] # электропочта отправителя
    # recipient_name = recipient_email # имя получателя | заминил на email получателя
    # recipient_email = 'to@you.ru' # электропочта получателя
    password = config['EMAIL']['SENDER_PASSWORD']
    # письмо в html
    # message_text ="""<strong>Письмо с html-тегами</strong>
    
    email_host = config['EMAIL']['EMAIL_HOST']
    email_port = config['EMAIL']['EMAIL_PORT']
    
    
    

    
    # формируем письмо
    msg = MIMEMultipart('related')
    msg['Subject'] = mkh([(subj, 'UTF-8')])
    msg['Date'] = formatdate(localtime=True)
    msg['Organization'] = mkh([(org,'UTF-8')])
    msg['Message-ID'] = msgid(domain='pravim.by', idstring=msg_id)
    

    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = ", ".join(recipient_emails)
    
    
    # # То, чего будет не видно, если почтовая программа поддерживает MIME
    # msg.preamble = "This is a multi-part message in MIME format."
    # msg.epilogue = "End of message"
    
    # Текстовая часть сообщения
    #---------------------------------------------------------------------------------------------------
    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)
    # msgText = MIMEText('Отправка писем с помощью Python',"","UTF-8")
    # msgAlternative.attach(msgText)
    
    # присоединяем HTML
    #----------------------------------------------------------------------------------------------------
    to_attach = MIMEText(message_text,"html","UTF-8")
    msgAlternative.attach(to_attach)
    

    
    # Отправка
    #---------------------------------------------------------------------------------------------------------------
    # Отправка письма


    # try:
    with smtplib.SMTP_SSL(email_host, email_port) as server:
        server.login(sender_email, password)
        server.sendmail(to_addrs=recipient_emails, from_addr=sender_email, msg=msg.as_string())
    # except (smtplib.SMTPRecipientsRefused,
    #     smtplib.SMTPSenderRefused) as  ErrorMsg:
    #     print("Проблема с отправкой письма. Причина: %s" % ErrorMsg)


def generate_message(template: str, context) -> str:
    template = env.get_template(template)

    # Рендеринг шаблона с данными
    output = template.render(context=context)
    with open(f'admin_mail.html', 'w', encoding='utf-8') as f:
        f.write(output)
    return output