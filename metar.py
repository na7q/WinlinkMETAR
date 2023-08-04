import re
import time
import imapclient
import email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# Email settings
EMAIL = 'email@gmail.com'
PASSWORD = 'passcode'

TARGET_SUBJECT = 'METAR'  # The subject you're looking for
CHECK_INTERVAL = 30  # Check for new emails every 30 seconds

def get_text_from_email(email_message):
    text = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                text += part.get_payload(decode=True).decode("utf-8")
    else:
        text = email_message.get_payload(decode=True).decode("utf-8")
    return text

def extract_station_id(text):
    return text.strip().upper()

def fetch_metar_data(station_id):
    url = "https://beta.aviationweather.gov/cgi-bin/data/metar.php?ids=" + station_id
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

def send_email(subject, body, recipient):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL, PASSWORD)
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server.sendmail(EMAIL, recipient, msg.as_string())

def main():
    while True:
        with imapclient.IMAPClient('imap.gmail.com', use_uid=True) as client:
            client.login(EMAIL, PASSWORD)
            client.select_folder('INBOX')

            messages = client.search(['UNSEEN', 'SUBJECT', TARGET_SUBJECT])

            for msg_id in messages:
                raw_message = client.fetch([msg_id], ['RFC822'])[msg_id][b'RFC822']
                email_message = email.message_from_bytes(raw_message)
                
                from_ = email_message['From']
                body_text = get_text_from_email(email_message)
                
                station_id = extract_station_id(body_text)
                if station_id:
                    metar_data = fetch_metar_data(station_id)
                    if metar_data:
                        send_email("METAR", metar_data, from_)
                        print("METAR Data sent to the requester.")
                    else:
                        print("Failed to fetch METAR data.")
                else:
                    print("No Station ID found.")
                
                print('-' * 30)
        
#        print("Waiting", CHECK_INTERVAL, "seconds before checking for new emails again...")
        time.sleep(CHECK_INTERVAL)
    
if __name__ == "__main__":
    main()
