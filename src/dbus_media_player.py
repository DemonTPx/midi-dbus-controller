import dbus
from collections import namedtuple


class Track(namedtuple('PlayerProperties', ['artist', 'album_artist', 'album', 'title', 'track_number'])):
    def is_different_track(self, other) -> bool:
        return other is None or \
            self.artist != other.artist or \
            self.album_artist != other.album_artist or \
            self.title != other.title or \
            self.track_number != other.track_number

    @staticmethod
    def empty():
        return Track('', '', '', '', 0)


class DbusMediaPlayer:
    DBUS_PATH = '/org/mpris/MediaPlayer2'
    DBUS_NAME = 'org.mpris.MediaPlayer2'
    DBUS_PLAYER_NAME = 'org.mpris.MediaPlayer2.Player'

    def __init__(self, session_bus, bus_name, owner) -> None:
        self.bus_name = bus_name
        self.owner = owner
        self.name = bus_name.replace(self.DBUS_NAME + '.', '')
        self._proxy = session_bus.get_object(bus_name, self.DBUS_PATH)
        self._methods = dbus.Interface(self._proxy, self.DBUS_PLAYER_NAME)
        self._properties = dbus.Interface(self._proxy, 'org.freedesktop.DBus.Properties')

        identity = self._properties.Get(self.DBUS_NAME, 'Identity')
        if identity:
            self.name = identity

        self.name_lower = self.name.lower()

        self._on_properties_changed_callback = None
        self._proxy.connect_to_signal('PropertiesChanged', self._on_properties_changed_wrapper)

    def stop(self) -> None:
        self._methods.Stop()

    def play(self) -> None:
        self._methods.Play()

    def play_pause(self) -> None:
        self._methods.PlayPause()

    def previous(self) -> None:
        self._methods.Previous()

    def next(self) -> None:
        self._methods.Next()

    def fetch_properties(self) -> (str, Track):
        playback_status = self._properties.Get(self.DBUS_PLAYER_NAME, 'PlaybackStatus')
        metadata = self._properties.Get(self.DBUS_PLAYER_NAME, 'Metadata')

        return playback_status, self._create_track(metadata)

    def set_on_properties_changed_callback(self, callback: callable) -> None:
        self._on_properties_changed_callback = callback

    def _on_properties_changed_wrapper(self, sender, props, extra) -> None:
        playback_status = None
        track = None

        if 'PlaybackStatus' in props:
            playback_status = props['PlaybackStatus']
        if 'Metadata' in props:
            track = self._create_track(props['Metadata'])

        if self._on_properties_changed_callback:
            self._on_properties_changed_callback(playback_status, track)

    def _create_track(self, metadata) -> Track:
        return Track(
            self._get_meta_first_or(metadata, 'xesam:artist', ''),
            self._get_meta_first_or(metadata, 'xesam:albumArtist', ''),
            self._get_meta_or(metadata, 'xesam:album', ''),
            self._get_meta_or(metadata, 'xesam:title', ''),
            self._get_meta_or(metadata, 'xesam:trackNumber', 0)
        )

    def _get_meta_or(self, metadata, key, default):
        if key in metadata:
            return metadata[key]

        return default

    def _get_meta_first_or(self, metadata, key, default):
        if key in metadata and len(metadata[key]) != 0:
            return metadata[key][0]

        return default
