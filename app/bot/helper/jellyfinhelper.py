import requests
import random
import string

import app.bot.helper.jellyfinhelper as jelly

def add_user(jellyfin_url, jellyfin_api_key, username, password, jellyfin_libs):
    try:
        url = f"{jellyfin_url}/Users/New"

        querystring = {"api_key":jellyfin_api_key}
        payload = {
            "Name": username,
            "Password": password
        }
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        userId = response.json()["Id"]

        if response.status_code != 200:
            print(f"Fehler beim erstellen des Jellyfin Benutzers: {response.text}")
            return False
        
        # Grant access to User
        url = f"{jellyfin_url}/Users/{userId}/Policy"

        querystring = {"api_key":jellyfin_api_key}

        enabled_folders = []
        server_libs = get_libraries(jellyfin_url, jellyfin_api_key)
        
        if jellyfin_libs[0] != "all":
            for lib in jellyfin_libs:
                found = False
                for server_lib in server_libs:
                    if lib == server_lib['Name']:
                        enabled_folders.append(server_lib['ItemId'])
                        found = True
                if not found:
                    print(f"Couldn't find Jellyfin Library: {lib}")

        payload = {
            "IsAdministrator": False,
            "IsHidden": True,
            "IsDisabled": False,
            "BlockedTags": [],
            "EnableUserPreferenceAccess": True,
            "AccessSchedules": [],
            "BlockUnratedItems": [],
            "EnableRemoteControlOfOtherUsers": False,
            "EnableSharedDeviceControl": True,
            "EnableRemoteAccess": True,
            "EnableLiveTvManagement": True,
            "EnableLiveTvAccess": True,
            "EnableMediaPlayback": True,
            "EnableAudioPlaybackTranscoding": True,
            "EnableVideoPlaybackTranscoding": True,
            "EnablePlaybackRemuxing": True,
            "ForceRemoteSourceTranscoding": False,
            "EnableContentDeletion": False,
            "EnableContentDeletionFromFolders": [],
            "EnableContentDownloading": True,
            "EnableSyncTranscoding": True,
            "EnableMediaConversion": True,
            "EnabledDevices": [],
            "EnableAllDevices": True,
            "EnabledChannels": [],
            "EnableAllChannels": False,
            "EnabledFolders": enabled_folders,
            "EnableAllFolders": jellyfin_libs[0] == "all",
            "InvalidLoginAttemptCount": 0,
            "LoginAttemptsBeforeLockout": -1,
            "MaxActiveSessions": 0,
            "EnablePublicSharing": True,
            "BlockedMediaFolders": [],
            "BlockedChannels": [],
            "RemoteClientBitrateLimit": 0,
            "AuthenticationProviderId": "Jellyfin.Server.Implementations.Users.DefaultAuthenticationProvider",
            "PasswordResetProviderId": "Jellyfin.Server.Implementations.Users.DefaultPasswordResetProvider",
            "SyncPlayAccess": "CreateAndJoinGroups"
        }
        headers = {"content-type": "application/json"}

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

        if response.status_code == 200 or response.status_code == 204:
            return True
        else:
            print(f"❌  Fehler beim vergeben der Rechte an den Benutzer: {response.text}")

    except Exception as e:
        print(e)
        return False


def get_libraries(jellyfin_url, jellyfin_api_key):
    url = f"{jellyfin_url}/Library/VirtualFolders"
    querystring = {"api_key":jellyfin_api_key}
    response = requests.request("GET", url, params=querystring)

    return  response.json()
    

def verify_username(jellyfin_url, jellyfin_api_key, username):
    users = get_users(jellyfin_url, jellyfin_api_key)
    valid = True
    for user in users:
        if user['Name'] == username:
            valid = False
            break

    return valid

def remove_user(jellyfin_url, jellyfin_api_key, jellyfin_username):
    try:
        # Get User ID
        users = get_users(jellyfin_url, jellyfin_api_key)
        userId = None
        for user in users:
            if user['Name'].lower() == jellyfin_username.lower():
                userId = user['Id']
        
        if userId is None:
            # User not found
            print(f"❌  Benutzer konnte nicht gelöscht werden, -mgs:{jellyfin_username}msg- von Jellyfin: Benutzer nicht gefunden.")
            return False
        
        # Delete User
        url = f"{jellyfin_url}/Users/{userId}"

        querystring = {"api_key":jellyfin_api_key}
        response = requests.request("DELETE", url, params=querystring)

        if response.status_code == 204 or response.status_code == 200:
            return True
        else:
            print(f"❌  Benutzer konnte nicht gelöscht werden: {response.text}")
    except Exception as e:
        print(e)
        return False

def reset_pw(jellyfin_url, jellyfin_api_key, jellyfin_username, password):
    try:
        # Get User ID
        users = get_users(jellyfin_url, jellyfin_api_key)
        userId = None
        for user in users:
            if user['Name'].lower() == jellyfin_username.lower():
                userId = user['Id']

        if userId is None:
            # User not found
            print(f"❌  Passwort zurücksetzen fehlgeschlagen: {jellyfin_username} nicht gefunden.")
            return False

        url = f"{jellyfin_url}/Users/{userId}/Password"
        querystring = {"api_key":jellyfin_api_key}
        data = {
            "CurrentPwd": "",
            "NewPw": password
        }
        headers = {"Content-Type": "application/json"}

        response = requests.request("POST", url, json=data, headers=headers, params=querystring)
        if response.status_code == 204:
            print("✅  Passwort zurückgesetzt")
            return True
        else:
            print(f"❌  Fehler beim Passwort resetten: {response.text}")
            return False

    except Exception as e:
        print(e)
        return False
 
def enable_user(jellyfin_url, jellyfin_api_key, jellyfin_username):
    try:
        # Get User ID
        users = get_users(jellyfin_url, jellyfin_api_key)
        userId = None
        for user in users:
            if user['Name'].lower() == jellyfin_username.lower():
                userId = user['Id']
        
        if userId is None:
            # User not found
            print(f"⚠️   Kein Account mit dieser Discord ID verknüpft: {jellyfin_username}")
            return False
        
        url = f"{jellyfin_url}/Users/{userId}/Policy"
        querystring = {"api_key":jellyfin_api_key}
        data = {
        "IsDisabled": False,
        "AuthenticationProviderId": "Jellyfin.Server.Implementations.Users.DefaultAuthenticationProvider",
        "PasswordResetProviderId": "Jellyfin.Server.Implementations.Users.DefaultPasswordResetProvider"
        }
        headers = {"Content-Type": "application/json"}

        response = requests.request("POST", url, json=data, headers=headers, params=querystring)
        if response.status_code == 204:
            print(f"✅  Benutzer wurde reaktiviert!")
            return True
        else:
            print(f"❌  Fehler beim reaktivieren: {response.text}")
            return False     
    except Exception as e:
        print(e)
        return False

def disable_user(jellyfin_url, jellyfin_api_key, jellyfin_username):
    try:
        # Get User ID
        users = get_users(jellyfin_url, jellyfin_api_key)
        userId = None
        for user in users:
            if user['Name'].lower() == jellyfin_username.lower():
                userId = user['Id']
        
        if userId is None:
            # User not found
            print(f"❌  Fehler beim deaktivieren des Accounts {jellyfin_username}, User nicht gefunden.")
            return False
        
        url = f"{jellyfin_url}/Users/{userId}/Policy"
        querystring = {"api_key":jellyfin_api_key}
        data = {
        "IsDisabled": True,
        "AuthenticationProviderId": "Jellyfin.Server.Implementations.Users.DefaultAuthenticationProvider",
        "PasswordResetProviderId": "Jellyfin.Server.Implementations.Users.DefaultPasswordResetProvider"
        }
        headers = {"Content-Type": "application/json"}

        response = requests.request("POST", url, json=data, headers=headers, params=querystring)
        if response.status_code == 204:
            print("✅  Benutzer wurde erfolgreich deaktiviert.")
            return True
        else:
            print(f"❌  Fehler beim deaktivieren des Benutzers: {response.text}")
            return False     
    except Exception as e:
        print(e)
        return False
       
def get_users(jellyfin_url, jellyfin_api_key):
    url = f"{jellyfin_url}/Users"

    querystring = {"api_key":jellyfin_api_key}
    response = requests.request("GET", url, params=querystring)

    return response.json()

def generate_password(length, lower=True, upper=True, numbers=True, symbols=True):
    character_list = []
    if not (lower or upper or numbers or symbols):
        raise ValueError("⚠️  Mindestens ein Zeichentyp muss angegeben werden")
        
    if lower:
        character_list += string.ascii_lowercase
    if upper:
        character_list += string.ascii_uppercase
    if numbers:
        character_list += string.digits
    if symbols:
        character_list += string.punctuation

    return "".join(random.choice(character_list) for i in range(length))

def get_config(jellyfin_url, jellyfin_api_key):
    url = f"{jellyfin_url}/System/Configuration"

    querystring = {"api_key":jellyfin_api_key}
    response = requests.request("GET", url, params=querystring, timeout=5)
    return response.json()

def get_status(jellyfin_url, jellyfin_api_key):
    url = f"{jellyfin_url}/System/Configuration"

    querystring = {"api_key":jellyfin_api_key}
    response = requests.request("GET", url, params=querystring, timeout=5)
    return response.status_code