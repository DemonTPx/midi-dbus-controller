from collections import namedtuple

class PlayerProperties(namedtuple('PlayerProperties', ['playback_status', 'album_artist', 'album', 'title', 'track_number'])):
    pass
