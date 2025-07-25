import imaplib
import email
import time
import requests
import html

# Email credentials
EMAIL = ''
APP_PASSWORD = ''
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993

# Telegram bot credentials
TELEGRAM_TOKEN = ''
TELEGRAM_CHAT_ID = ''

# Track already seen email UIDs during runtime
seen_uids = set()

def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        if not response.ok:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def decode_payload(payload):
    try:
        return payload.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return payload.decode('ISO-8859-1')
        except:
            return "[Could not decode message body]"

def check_mail():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL, APP_PASSWORD)
        mail.select('inbox')

        status, messages = mail.search(None, '(UNSEEN)')
        if status != "OK":
            print("Failed to retrieve messages.")
            return

        for num in messages[0].split():
            # Get UID of the email
            status, uid_data = mail.fetch(num, '(UID)')
            if status != 'OK':
                continue
            uid_line = uid_data[0].decode()
            uid = uid_line.split('UID ')[1].split(' ')[0]

            if uid in seen_uids:
                continue
            seen_uids.add(uid)

            typ, data = mail.fetch(num, '(RFC822)')
            if typ != 'OK':
                continue

            msg = email.message_from_bytes(data[0][1])

            # Parse "From" and "Subject"
            from_ = html.escape(msg.get("From", ""))
            subject = html.escape(msg.get("Subject", ""))

            # Parse message body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and not part.get('Content-Disposition'):
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = decode_payload(payload)
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = decode_payload(payload)

            preview = html.escape(body.strip().replace('\r', '').replace('\n', ' ')[:300])

            telegram_msg = f"<b>📬 New Email</b>\n<b>From:</b> {from_}\n<b>Subject:</b> {subject}\n\n{preview}"
            send_to_telegram(telegram_msg)

        mail.logout()

    except Exception as e:
        print(f"❌ Error: {e}")

# Main loop
if __name__ == "__main__":
    while True:
        check_mail()
        time.sleep(30)  # Check every 30 seconds
