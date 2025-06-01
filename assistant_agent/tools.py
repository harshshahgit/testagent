# assistant_agent/tools.py
import os
import datetime # Keep for CalendarTool
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Constants for Google Calendar Tool ---
SCOPES_CALENDAR = ['https://www.googleapis.com/auth/calendar']
TOKEN_JSON_PATH_CALENDAR = 'token_calendar.json'

# --- Constants for Google Drive Tool ---
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive.metadata.readonly'] # Start with read-only metadata
TOKEN_JSON_PATH_DRIVE = 'token_drive.json'
# Common path for OAuth 2.0 client secrets file (expected from GOOGLE_APPLICATION_CREDENTIALS)
# CREDENTIALS_JSON_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') # Loaded dynamically

class BaseTool:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def execute(self, action: str, params: dict):
        raise NotImplementedError("Each tool must implement the execute method.")

class GoogleCalendarTool(BaseTool): # Keep existing CalendarTool implementation
    def __init__(self):
        super().__init__(
            name="GoogleCalendarTool",
            description="Tool for interacting with Google Calendar to find events, create meetings, etc."
        )
        self.service = None
        self._ensure_service()

    def _ensure_service(self):
        if self.service is None:
            self.service = self._get_calendar_service()

    def _get_calendar_service(self):
        creds = None
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if not credentials_path:
            print("ERROR (CalendarTool): GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set for CalendarTool.")

        if os.path.exists(TOKEN_JSON_PATH_CALENDAR):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_JSON_PATH_CALENDAR, SCOPES_CALENDAR)
            except Exception as e:
                print(f"Warning (CalendarTool): Could not load token from {TOKEN_JSON_PATH_CALENDAR}: {e}")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("Info (CalendarTool): Refreshing expired credentials...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error (CalendarTool): Failed to refresh credentials: {e}")
                    creds = None
            else:
                creds = None

            if not creds:
                print(f"Info (CalendarTool): Running OAuth 2.0 flow using credentials from {credentials_path}")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES_CALENDAR)
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    print(f"ERROR (CalendarTool): Credentials file not found at {credentials_path}.")
                    raise
                except Exception as e:
                    print(f"Error (CalendarTool): OAuth flow failed: {e}")
                    raise

            try:
                with open(TOKEN_JSON_PATH_CALENDAR, 'w') as token_file:
                    token_file.write(creds.to_json())
                print(f"Info (CalendarTool): Credentials saved to {TOKEN_JSON_PATH_CALENDAR}")
            except Exception as e:
                print(f"Error (CalendarTool): Could not save token to {TOKEN_JSON_PATH_CALENDAR}: {e}")

        try:
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            print(f"Error (CalendarTool): Failed to build calendar service: {e}")
            raise

    def _parse_datetime_params(self, params: dict) -> tuple[str | None, str | None]:
        start_dt_str = params.get("start_time") or params.get("date_time")
        end_dt_str = params.get("end_time")
        if start_dt_str:
            try:
                datetime.datetime.fromisoformat(start_dt_str.replace("Z", "+00:00"))
            except ValueError:
                print(f"Warning (CalendarTool): start_dt_str '{start_dt_str}' is not ISO. Tool may fail.")
        if end_dt_str:
            try:
                datetime.datetime.fromisoformat(end_dt_str.replace("Z", "+00:00"))
            except ValueError:
                 print(f"Warning (CalendarTool): end_dt_str '{end_dt_str}' is not ISO. Tool may fail.")
        return start_dt_str, end_dt_str

    def execute(self, action: str, params: dict) -> str:
        self._ensure_service()
        if not self.service:
            return "Error: Google Calendar service not available."
        try:
            if action == "find_events":
                now = datetime.datetime.utcnow()
                time_min_str = params.get('timeMin')
                time_max_str = params.get('timeMax')
                single_date_str = params.get('date_time')

                if not time_min_str and single_date_str:
                    try:
                        dt_obj = datetime.datetime.fromisoformat(single_date_str.split('T')[0] + "T00:00:00")
                        time_min_str = dt_obj.isoformat() + 'Z'
                        time_max_str = (dt_obj + datetime.timedelta(days=1)).isoformat() + 'Z'
                    except ValueError:
                         print(f"Warning (CalendarTool): Could not parse single_date_str '{single_date_str}' for find_events.")
                         time_min_str = now.isoformat() + 'Z'
                         time_max_str = (now + datetime.timedelta(days=7)).isoformat() + 'Z'
                elif not time_min_str:
                    time_min_str = now.isoformat() + 'Z'

                events_result = self.service.events().list(
                    calendarId='primary', timeMin=time_min_str, timeMax=time_max_str,
                    maxResults=10, singleEvents=True, orderBy='startTime'
                ).execute()
                events = events_result.get('items', [])
                if not events: return "No upcoming events found for the specified period."
                output = "Found events:\n"
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    output += f"- {event['summary']} (Starts: {start})\n"
                return output.strip()
            elif action == "create_event":
                summary = params.get('event_summary', 'New Event from Assistant')
                start_time_str, end_time_str = self._parse_datetime_params(params)
                if not start_time_str: return "Error: Start time not provided for creating event."
                if not end_time_str:
                    try:
                        start_dt = datetime.datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                        end_dt = start_dt + datetime.timedelta(hours=1)
                        end_time_str = end_dt.isoformat()
                    except ValueError: return f"Error: Invalid start_time format '{start_time_str}'."
                event_body = {
                    'summary': summary,
                    'start': {'dateTime': start_time_str, 'timeZone': params.get('timeZone', 'UTC')},
                    'end': {'dateTime': end_time_str, 'timeZone': params.get('timeZone', 'UTC')},
                }
                if 'attendees' in params and isinstance(params['attendees'], list):
                    event_body['attendees'] = [{'email': email} for email in params['attendees'] if isinstance(email, str)]
                if 'location' in params: event_body['location'] = params['location']
                created_event = self.service.events().insert(calendarId='primary', body=event_body).execute()
                return f"Event created: {created_event.get('summary')} - Link: {created_event.get('htmlLink')}"
            else: return f"Error: Action '{action}' not supported by GoogleCalendarTool."
        except HttpError as error: return f"An API error occurred (GoogleCalendarTool): {error.resp.status} - {error._get_reason()}"
        except Exception as e: return f"An unexpected error occurred (GoogleCalendarTool): {str(e)}"


class GoogleDriveTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="GoogleDriveTool",
            description="Tool for interacting with Google Drive to search files, download documents, etc."
        )
        self.service = None
        self._ensure_service()

    def _ensure_service(self):
        if self.service is None:
            self.service = self._get_drive_service()

    def _get_drive_service(self):
        creds = None
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if not credentials_path:
            print("ERROR (DriveTool): GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set for DriveTool.")

        if os.path.exists(TOKEN_JSON_PATH_DRIVE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_JSON_PATH_DRIVE, SCOPES_DRIVE)
            except Exception as e:
                print(f"Warning (DriveTool): Could not load token from {TOKEN_JSON_PATH_DRIVE}: {e}")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("Info (DriveTool): Refreshing expired credentials...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error (DriveTool): Failed to refresh credentials: {e}")
                    creds = None
            else:
                creds = None

            if not creds: # If still no valid credentials, run the OAuth flow
                print(f"Info (DriveTool): Running OAuth 2.0 flow for Drive using credentials from {credentials_path}")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES_DRIVE)
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    print(f"ERROR (DriveTool): Credentials file not found at {credentials_path}. "
                          "Ensure GOOGLE_APPLICATION_CREDENTIALS points to your client_secret.json.")
                    raise
                except Exception as e:
                    print(f"Error (DriveTool): OAuth flow failed: {e}")
                    raise

            try:
                with open(TOKEN_JSON_PATH_DRIVE, 'w') as token_file:
                    token_file.write(creds.to_json())
                print(f"Info (DriveTool): Drive credentials saved to {TOKEN_JSON_PATH_DRIVE}")
            except Exception as e:
                print(f"Error (DriveTool): Could not save token to {TOKEN_JSON_PATH_DRIVE}: {e}")

        try:
            service = build('drive', 'v3', credentials=creds)
            return service
        except Exception as e:
            print(f"Error (DriveTool): Failed to build drive service: {e}")
            raise

    def execute(self, action: str, params: dict) -> str:
        self._ensure_service()
        if not self.service:
            return "Error: Google Drive service not available."

        try:
            if action == "search_files":
                # LLM params examples:
                # {"file_name": "report.pdf"}
                # {"query_terms": "meeting notes Q3", "mime_type": "application/vnd.google-apps.document"}
                # {"shared_with_me": true, "owner": "user@example.com"}

                query_parts = []
                file_name = params.get("file_name")
                query_terms = params.get("query_terms")
                mime_type = params.get("mime_type")

                if file_name:
                    query_parts.append(f"name contains '{file_name.replace("'", "\'")}'") # Escape single quotes
                if query_terms:
                    query_parts.append(f"fullText contains '{query_terms.replace("'", "\'")}'")
                if mime_type:
                    query_parts.append(f"mimeType = '{mime_type.replace("'", "\'")}'")

                # Default to searching user's files, not trashed
                query_parts.append("trashed = false")

                if not query_parts:
                    return "Error: No search parameters (file_name, query_terms, mime_type) provided for search_files."

                drive_query = " and ".join(query_parts)
                print(f"Info (DriveTool): Searching Drive with query: '{drive_query}'")

                results = self.service.files().list(
                    q=drive_query,
                    pageSize=10, # Max 10 results for now
                    fields="nextPageToken, files(id, name, webViewLink, mimeType, modifiedTime, owners)"
                ).execute()

                items = results.get('files', [])
                if not items:
                    return "No files found matching your criteria."

                output = "Found Drive files:\n"
                for item in items:
                    owners = ", ".join([owner.get('displayName', owner.get('emailAddress', 'Unknown Owner')) for owner in item.get('owners', [])])
                    output += f"- {item['name']} (Type: {item.get('mimeType', 'N/A')}, Last Modified: {item.get('modifiedTime', 'N/A')}, Owners: {owners})\n  Link: {item.get('webViewLink', 'N/A')}\n"
                return output.strip()

            else:
                return f"Error: Action '{action}' not supported by GoogleDriveTool."

        except HttpError as error:
            return f"An API error occurred (GoogleDriveTool): {error.resp.status} - {error._get_reason()}"
        except Exception as e:
            # Log the full traceback for unexpected errors for easier debugging
            import traceback
            print(f"ERROR (DriveTool): Unexpected error during execute: {str(e)}\n{traceback.format_exc()}")
            return f"An unexpected error occurred (GoogleDriveTool): {str(e)}"


# --- Placeholder for PresentationTool ---
class PresentationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="PresentationTool",
            description="Tool for preparing presentations, possibly using Google Slides or other services."
        )
    def execute(self, action: str, params: dict) -> str:
        return f"Placeholder: PresentationTool action '{action}' executed with params '{params}'."


if __name__ == '__main__':
    # Test GoogleCalendarTool (existing test)
    # ... (calendar tool tests - keep as is)

    # Test GoogleDriveTool (requires GOOGLE_APPLICATION_CREDENTIALS to be set
    # and user interaction for the first-time OAuth flow for Drive)
    print("\n--- Testing GoogleDriveTool ---")
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Skipping GoogleDriveTool test: GOOGLE_APPLICATION_CREDENTIALS not set.")
    else:
        try:
            drive_tool = GoogleDriveTool()

            # Test 1: Search for files by name (example)
            # LLM would generate these params based on "find my document named annual_report.pdf"
            print("\nTest: Searching Drive for files...")
            search_params_name = {"file_name": "Getting started"} # A common default file in Google Drive
            files_found_name = drive_tool.execute(action="search_files", params=search_params_name)
            print(f"Result of search_files (by name 'Getting started'):\n{files_found_name}")

            # Test 2: Search by query terms
            search_params_terms = {"query_terms": "introduction"}
            files_found_terms = drive_tool.execute(action="search_files", params=search_params_terms)
            print(f"\nResult of search_files (by terms 'introduction'):\n{files_found_terms}")

            # Test 3: Search by mimeType (example: Google Docs)
            search_params_mime = {"mime_type": "application/vnd.google-apps.document", "query_terms": "test"}
            files_found_mime = drive_tool.execute(action="search_files", params=search_params_mime)
            print(f"\nResult of search_files (Google Docs with 'test'):\n{files_found_mime}")

        except Exception as e:
            print(f"Error during GoogleDriveTool test: {e}")
            print("Ensure GOOGLE_APPLICATION_CREDENTIALS is set correctly and you have completed the OAuth flow for Drive if prompted.")
