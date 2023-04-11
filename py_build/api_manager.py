import requests
import json
import configparser
import hashlib
from alive_progress import alive_bar
from pprint import pprint

config = configparser.ConfigParser()
config.read("config.ini")


# # entry
# def maine():
#     userID = get_UserId()
#     accessToken =  get_WebAccessToken(config["creds"]["spDcCookie"])
#     generate_song_list(userID, accessToken)


def get_song_list(sp):
    userID = get_UserId(sp)
    accessToken = get_WebAccessToken(config["creds"]["spDcCookie"])
    return generate_song_list(userID, accessToken, sp)


# get the authenticated users ID
def get_UserId(sp):
    results = sp.current_user()
    return results["id"]


"""
gets all friends, then their playlists, then their playlists songs

args:
    (str)      userID: authenticated users id
    (srt) accessToken: token used to make naughty calls
"""


def generate_song_list(userID, accessToken, sp):
    # returns a dict with all friends names/uri's, uri is the key
    translation_table = dict()
    friends = get_friend_list(accessToken, userID)

    non_friend_list = []
    for friend in friends:
        print(friend)
        result = get_playlist_from_user(accessToken, friend)
        if result == 0:
            non_friend_list.append(friend)
        else:
            friends[friend]["playlists"] = result
            for playlist in result:
                playlist_uri = playlist["uri"].split(":")[-1]
                translation_table[playlist_uri] = friend

    for artist in non_friend_list:
        del friends[artist]

    playlistList = get_all_playlists(friends, sp)
    return cycle_through_playlists(playlistList, sp)


def get_all_playlists(friends, sp):
    playlistList = []
    with alive_bar(len(friends)) as bar:
        print("getting playlists")
        for friend in friends:
            bar()
            for playlist in friends[friend]["playlists"]:
                playlistList.append(get_playlist(playlist["uri"], sp))
    return playlistList


def cycle_through_playlists(playlistList, sp):
    song_list = dict()
    people_list = dict()
    playlist_list = dict()
    # playlistList is a list of all the returned get_playlist things in one place, so each iteration is a new playlist

    with alive_bar(len(playlistList)) as bar:
        print("filtering playlists")
        for playlist in playlistList:
            bar()
            tracklist = playlist["tracks"]["items"]
            next_holder = playlist["tracks"]
            while next_holder["next"]:
                next_holder = sp.next(next_holder)
                tracklist.extend(next_holder["items"])

            if playlist["uri"] not in playlist_list.keys():
                playlist_list[playlist["uri"]] = playlist
                del playlist_list[playlist["uri"]]["tracks"]

            FriendID = playlist["owner"]["id"]
            for song in tracklist:
                if FriendID == "spotify":
                    break
                if FriendID not in people_list.keys():
                    people_list[FriendID] = sp.user(FriendID)
                # again any ref to this is just getting info for iterative song
                SongInfoLocation = song["track"]
                if SongInfoLocation != None:
                    song_hash_combination = SongInfoLocation["name"]
                    for artist in SongInfoLocation["artists"]:
                        song_hash_combination += " " + artist["name"]
                    song_hash = hashlib.md5(song_hash_combination.encode()).hexdigest()

                    if song_hash not in song_list.keys():
                        # both track and album have available_markets like a bunch of bastards
                        del SongInfoLocation["available_markets"]
                        del SongInfoLocation["album"]["available_markets"]

                        # initizaliation of the song list, with URI as the key
                        song_list[song_hash] = {
                            "song_info": SongInfoLocation,
                            "origins": {FriendID: {}},
                        }
                        # array must be initalized outside of brackets
                        song_list[song_hash]["origins"][FriendID]["PlaylistArray"] = [
                            playlist["uri"]
                        ]

                    else:
                        # until this point i have been unable to test how
                        if FriendID not in song_list[song_hash]["origins"].keys():
                            song_list[song_hash]["origins"][FriendID] = {}
                            song_list[song_hash]["origins"][FriendID][
                                "PlaylistArray"
                            ] = [playlist["uri"]]
                        else:
                            # print(song_list[song_hash]['origins'][FriendID]['PlaylistArray'])
                            if (
                                playlist["uri"]
                                not in song_list[song_hash]["origins"][FriendID][
                                    "PlaylistArray"
                                ]
                            ):
                                song_list[song_hash]["origins"][FriendID][
                                    "PlaylistArray"
                                ].append(playlist["uri"])
    return song_list, people_list, playlist_list


"""
pass in a uri, returns all the songs in the playlist

args:
    (str) uri of the playlist, eg 'spotify:playlist:4Fkepy5Zx31h8BgIwvDaHl'
returns:
    (dict) dict of all songs in the playlist
"""


def get_playlist(uri, sp):
    playlist_url = uri.split(":")[-1]
    playlist = sp.playlist(playlist_url)
    return playlist


"""
use the sp_dc to get an access token

args:
    (str) spDcCookie, mmm cookie
returns:
    (str) accessToken, used for naughty calls
"""


def get_WebAccessToken(spDcCookie):
    url = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
    headers = {"Cookie": f"sp_dc={spDcCookie}"}
    response = requests.get(url, headers=headers)
    return json.loads(response.text)["accessToken"]


"""
get the friend list of the passed ID

args:
    (str) webAccessToken: used for naughty calls
    (str)         userID: used to specify the user
returns:
    (dict)       friends: a dict of all found friends
"""


def get_friend_list(webAccessToken, userID):
    return {
        "1162936152": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee85b95d76b7abf00a418e0dd07c",
            "name": "Tim Antumbra",
        },
        "8fziw0sfehsukj5ix8rlwzd1l": {"name": "FtpApoc"},
        "atj4y7wyuawsuc2zhl90zcw7h": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee857f680082f4f816cf7072e4e7",
            "name": "WeirdNoodle",
        },
        "d2gvezbrb7ciwmtals4s6ovsf": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee859c56405bd97d523bb217c195",
            "name": "Joe Day",
        },
        "dafydd.morris17": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee85f519bec6cb87e07d524ee6a9",
            "name": "Dafydd Morris",
        },
        "micharamshaw": {
            "image_url": "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=322856178156560&height=300&width=300&ext=1683589629&hash=AeQ8ISFU2y_g1bkqF1A",
            "name": "Michelle Ramshaw",
        },
        "sws2obne5rwglf9x7podxy3nb": {
            "image_url": "",
            "name": "henry",
        },
        "whiteroseisotp": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee85d31c3b2b29387115cb336df7",
            "name": "Ellie",
        },
        "atrs626": {
            "image_url": "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=1754867604750626&height=300&width=300&ext=1683651933&hash=AeSBvSJPC64kAaeDzcw",
            "name": "Adam Stephens",
        },
        "hungryrussianft": {"name": "hungryrussianft"},
    }


# def get_friend_list(webAccessToken, userID):
#     friends = dict()
#     url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{userID}/following"
#     headers = {"Authorization": f"Bearer {webAccessToken}"}
#     response = requests.get(url, headers=headers)
#     print(response)
#     json_friend_list = json.loads(response.text)
#     for friend in json_friend_list["profiles"]:
#         friend_id = friend["uri"].split(":")[-1]
#         friends[friend_id] = dict()
#         friends[friend_id]["name"] = friend["name"]
#         if "image_url" in friend:
#             friends[friend_id]["image_url"] = friend["image_url"]
#     pprint(friends)
#     return friends


"""
get all playlists from a user

args:
    (str)          webAccessToken: used for naughty calls
    (str)                  userID: used to specify the user
returns:
    (dict)       public_playlists: a dict of all public playlists
"""


def get_playlist_from_user(webAccessToken, userID):
    url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{userID}?playlist_limit=10&artist_limit=10&episode_limit=10&market=from_token"
    headers = {"Authorization": f"Bearer {webAccessToken}"}
    response = requests.get(url, headers=headers)
    try:
        json_response = json.loads(response.text)
        if "public_playlists" in json_response:
            return json_response["public_playlists"]
        else:
            return {}
    except ValueError as e:
        return 0
