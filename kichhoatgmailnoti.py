from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ==== CẤU HÌNH ==== #
ACCESS_TOKEN = "AIzaSyCrQ_aTITEgJ0kU0PIhiPaPJVMh5qiz5HE"  # access token của bạn
    # project Google Cloud
TOPIC_NAME = f"projects/crawemail-469504/topics/notification"

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)  # mở browser login Gmail
service = build('gmail', 'v1', credentials=creds)

# Bây giờ creds có access_token + refresh_token + client_id + client_secret
response = service.users().watch(
    userId='me',
    body={
        "labelIds": ["INBOX"],
        "topicName": TOPIC_NAME
    }
).execute()

print(response)