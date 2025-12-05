import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_service():
    """Shows basic usage of the Blogger API.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secret.json'):
                raise FileNotFoundError("client_secret.json not found. Please download it from Google Cloud Console.")
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('blogger', 'v3', credentials=creds)
    return service

def get_blog_id(service):
    """Retrieves the Blog ID of the first blog associated with the account."""
    try:
        users = service.users().get(userId='self').execute()
        blogs = service.blogs().listByUser(userId=users['id']).execute()
        if 'items' in blogs:
            return blogs['items'][0]['id']
        else:
            print("No blogs found.")
            return None
    except Exception as e:
        print(f"Error getting blog ID: {e}")
        return None

def create_post(service, blog_id, title, content, labels=None):
    """Creates a new post on the specified blog."""
    body = {
        'title': title,
        'content': content,
    }
    if labels:
        body['labels'] = labels

    try:
        posts = service.posts()
        result = posts.insert(blogId=blog_id, body=body, isDraft=False).execute() # Publish directly
        print(f"Post created: {result['url']}")
        return result
    except Exception as e:
        print(f"Error creating post: {e}")
        if hasattr(e, 'content'):
            print(f"Error content: {e.content}")
        return None

if __name__ == "__main__":
    service = get_service()
    blog_id = get_blog_id(service)
    if blog_id:
        create_post(service, blog_id, "Test Post", "This is a test post from Python.", ["test", "python"])
