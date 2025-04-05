import base64
import json
import requests
import urllib.request
import re
import os
import yt_dlp
import urllib.parse


from dotenv import load_dotenv
load_dotenv()

from requests import post

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

readPullFile = open("dependencies/pullPlaylist.txt","r")
writePullFile = open("dependencies/pullPlaylist.txt","a")

#   Function to get session token from spotify API

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}
    result = post(url, headers = headers, data = data)

    json_result = json.loads(result.content)
    
    token = json_result["access_token"]

    return token

token = get_token()

#   Function to create authorisation header when token value is passed

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

#   Function to get the track names from the specified spotify playlist

def get_playlist_tracks(token, playlist_id):
    readInstalledFile = open("dependencies/installed.txt","r")
    writeInstalledFile = open("dependencies/installed.txt","a")

    # 首先获取播放列表信息
    playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id.split('?')[0]}"
    headers = get_auth_header(token)
    playlist_response = requests.get(playlist_url, headers=headers)
    playlist_data = playlist_response.json()
    playlist_name = playlist_data.get('name', 'Unknown Playlist')
    
    # 确保下载目录存在
    os.makedirs(f"downloaded/{playlist_name}", exist_ok=True)

    field = "fields=tracks.items(track(name, artists(name)))"
    url = f"https://api.spotify.com/v1/playlists/{playlist_id.split('?')[0]}?{field}"
    headers = get_auth_header(token)

    result = requests.get(url, headers = headers)
    print(f"Status Code: {result.status_code}")
    print(f"Response: {result.text}")
    
    try:
        json_response = result.json()
        if 'tracks' not in json_response:
            print("Error: 'tracks' field not found in response")
            print("Full response structure:", json_response.keys())
            return
        result = json_response['tracks']['items']
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    trackList = []
    alreadyInstalled = []
    new = []

    for track in readInstalledFile.readlines():
        alreadyInstalled.append(track)

    print("\n")
    print("--------START--------")

    for track in result:
        currentData = f"{track['track']['name']} - {track['track']['artists'][0]['name']}"
        print(currentData)
        trackList.append(currentData)

        if(f"{currentData}\n" not in alreadyInstalled):
            new.append(currentData)
            writeInstalledFile.writelines(f"{currentData}\n")

    print("---------END---------")
    print("\n")

    print("---------NEW---------")

    for track in new:
        print(f"New: {track}")
        get_youtube_link(track, playlist_name)

    print("---------------------")
    print("\n")

    readInstalledFile.close()
    writeInstalledFile.close()

#   Function to query Youtube API for the link to the top related video associated with the song name pulled from the spotify playlist
    
def get_youtube_link(track_name, playlist_name):
    # Properly encode the search keyword for URL
    search_keyword = urllib.parse.quote(track_name + " audio")
    
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    url = f"https://www.youtube.com/watch?v={video_ids[0]}"
    download_video(url, playlist_name)

# Function to download videos associated with the previously created links
    
def download_video(url, playlist_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'downloaded/{playlist_name}/%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

#   Function to clear the text file in which the pull-playlist ID is stored when ID is updated

def clearPullFile():
    writePullFile = open("dependencies/pullPlaylist.txt","w")
    writePullFile.close()
    writePullFile = open("dependencies/pullPlaylist.txt","a")

#   Function to clear file containing all previously installed songs when playlist ID is changed

def clearInstalledFile():
    writeInstalledFile = open("dependencies/installed.txt","w")
    writeInstalledFile.close()
    writeInstalledFile = open("dependencies/installed.txt","a")

#   This portion checks whether the playlist ID has been specified or not, but checking tho see whether the pullPlaylist file is
# is empty or not

first_char = readPullFile.read(1)

if not first_char:
    pullSet = False
    playlist_id = "4zjRKXhbBEkoz8iaDLhYKj?si=848546a7348b4514"

else:
    pullSet = True
    playlist_id = first_char + readPullFile.readline().strip()

#   Main program loop

print('Enter "?" to view help message')
print("\n")

while True:
    userCommand = input("spotil> ")

    if(userCommand == "set-id"):
        pullChange = input("Playlist ID: ")
        playlist_id = pullChange
        pullSet = True
        clearPullFile()
        writePullFile.write(pullChange)

    elif(userCommand == "pull"):
        if(pullSet == True):
            get_playlist_tracks(token, playlist_id)

        else:
            print("Pull playlist not set, default will be used (Use command 'pull-set' to specify playlist ID)")
            playlist_id = "4zjRKXhbBEkoz8iaDLhYKj?si=848546a7348b4514"
            get_playlist_tracks(token, playlist_id)

    elif(userCommand == "show-id"):
        print(f"Pull Playlist ID: {playlist_id}")

    elif(userCommand == "?"):
        print("\n")
        print(" =============================================================")
        print(" | set-id  -  Used to set the ID of the download playlist    |")
        print(" | show-id -  Used to show the current download playlist ID  |")
        print(" | pull    -  Used to download songs from specified playlist |")
        print(" | exit    -  Used to exit the program                       |")
        print(" =============================================================")
        print("\n")

        

    elif(userCommand == "exit"):
        print("Thank you for using :)")
        break