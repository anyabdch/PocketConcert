import statistics as stat
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ticketpy

prog_scope = "user-library-read playlist-modify-public user-top-read"

tm = ticketpy.ApiClient('udnmqgWoGMTELYeyQLvnwVIa6TC2pd4a')
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=prog_scope))

target_artists = {}
saved_songs = []
concert_name = ''
tm_artists = ['Leon Bridges'] #while I work on the front end, this is autofilled so the back end still works :)
user_vibe = {}
attributes = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'valence']

# user needs to input concert (a  get_concert_info())
def get_concert_info(name):
    global concert_name
    concert_name = name.capitalize()
    events = tm.events.find(keyword=name)
    if events.__len__() > 1:
        pass
         # print some sort of options TBD
    else:
         pass

#pulls all the albums by a given artist
def artist_albums_ids(artist_id):
    album_list = []
    temp = sp.artist_albums(artist_id)['items']
    for album in temp:
        album_list.append(album['id'])
    return album_list

# a helper function for checking if artist is in library
def current_user_listens_to_artist(artist_id):
    album_list = artist_albums_ids(artist_id)
    return sp.current_user_saved_albums_contains(album_list)

# a helper for converting artist name to artist id
def artist_to_id(artist):
    return sp.search(q=artist, type='artist')['artists']['items'][0]['id']

# F1: function that compares a list of artists (from ticketmaster) to user's library, returns matches

def find_common_artists():
    global target_artists
    for num, artist in enumerate(tm_artists):
        artist_id = artist_to_id(artist)
        if current_user_listens_to_artist(artist_id):
            target_artists[num] = {'artist': artist, 'artist_id': artist_id}
    print(target_artists)

# F2: function that returns all saved songs by specific artists
#    for artist in F1 : F2

def get_saved_songs():
    global target_artists
    global saved_songs
    for artist in target_artists:
        for album in artist_albums_ids(target_artists[artist]['artist_id']):
            for song in sp.album(album)['tracks']['items']:
                if sp.current_user_saved_tracks_contains([song['id']])[0]:
                    saved_songs.append(song['id'])

# F3: builds a playlist with F2 songs
def build_saved_playlist():
    global concert_name
    p_name = 'Saved Songs for '+concert_name
    p_description = 'A playlist of songs you listen to that might be played at '+concert_name
    if saved_songs.__len__() == 0:
        if tm_artists.__len__() == 1:
            print("It seems you don't have any of this artist's music saved!")
        else:
            print("It seems like you don't have any of these artists' songs saved!")
    else:
        sp.user_playlist_create(sp.me()['id'], name=p_name, description=p_description)
        sp.playlist_add_items(sp.user_playlists(sp.me()['id'], 1)['items'][0]['id'], saved_songs)

#new attempt of rec songs
def get_user_vibe():
    global user_vibe
    user_top = [song['id'] for song in sp.current_user_top_tracks()['items']]
    tracks = sp.audio_features(user_top)
    for attribute in attributes:
        data = [track[attribute] for track in tracks]
        user_vibe[attribute] = {'avg': stat.mean(data), 'var':  stat.stdev(data)}

def get_rec_songs(size):
    rec_songs = []
    if size == 'SMALL':
        var = 0.1
    elif size == 'MEDIUM':
        var = 0.4
    else:
        var = 0.8
    for artist in tm_artists:
        for album in sp.albums(artist_albums_ids(artist_to_id(artist)))['albums']:
            songs = [song['id'] for song in album['tracks']['items']]
            vibes = sp.audio_features(songs)
            in_library = sp.current_user_saved_tracks_contains(songs)
            for idx,vibe in enumerate(vibes):
                valid = True
                for attribute in attributes:
                    min = user_vibe[attribute]['avg'] - (var * user_vibe[attribute]['var'])
                    max = user_vibe[attribute]['avg'] + (var * user_vibe[attribute]['var'])
                    valid = min < vibe[attribute] < max
                if valid and not in_library[idx]:
                    rec_songs.append(songs[idx])
    return rec_songs

# # F4: somehow return a list of recommended songs using user library AND artists from tm (hopefully already a function)
# def get_spotify_rec_songs():
#     a_ids = [artist['id'] for artist in sp.current_user_top_artists(limit=3)['items']]
#     s_ids = [song['id'] for song in sp.current_user_top_tracks(limit=2)['items']]
#     recs = [track['id'] for track in sp.recommendations(a_ids, None, s_ids, 20, None, target_artists=target_artists)['tracks']]
#     for idx, song in enumerate(recs):
#         if sp.current_user_saved_tracks_contains(recs)[idx]:
#             recs.pop(idx)
#     return recs

# F6: builds a playlist with F4 songs
def build_recs_playlist(size):
    global concert_name
    p_name = 'Recommended Songs for '+concert_name
    p_description = "A playlist of songs you might like in case they're played at "+concert_name
    rec_songs = get_rec_songs(size)
    if rec_songs.__len__() == 0:
        print("Looks like our algorithm doesn't think you'll enjoy this concert. Hope you didn't buy tickets already...")
    while rec_songs.__len__() > 100:
        rec_songs.pop(random.randint(0, rec_songs.__len__()))
    else:
        sp.user_playlist_create(sp.me()['id'], name=p_name, description=p_description)
        sp.playlist_add_items(sp.user_playlists(sp.me()['id'], 1)['items'][0]['id'], rec_songs)

# run script:
def main(name,  size='SMALL'):
    # get_concert_info(name)  #again this is just while frontend is being built
    find_common_artists()
    get_saved_songs()
    get_user_vibe()
    build_saved_playlist()
    build_recs_playlist(size)

main(name=input('Please enter the name of the festival/concert'), size='PLease enter the size of playlist you\'d like')
#regardless of what you put for input right now all you'll get is Leon Bridges :)

#future events?
#seatgeek: 4c57e87051e981580777bdde21a0279a8fb8ace04bc02e4f150df342d6099ac6
