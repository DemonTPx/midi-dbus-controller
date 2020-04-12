import dbus
from collections import namedtuple


class PlayerProperties(namedtuple('PlayerProperties', ['playback_status', 'artist', 'album_artist', 'album', 'title', 'track_number'])):
    def is_different_track(self, other) -> bool:
        return other is None or \
            self.artist != other.artist or \
            self.album_artist != other.album_artist or \
            self.title != other.title or \
            self.track_number != other.track_number


class DbusMediaPlayer:
    DBUS_PATH = '/org/mpris/MediaPlayer2'
    DBUS_NAME = 'org.mpris.MediaPlayer2'
    DBUS_PLAYER_NAME = 'org.mpris.MediaPlayer2.Player'

    def __init__(self, session_bus, name) -> None:
        bus_name = self.DBUS_NAME + '.' + name
        self._proxy = session_bus.get_object(bus_name, self.DBUS_PATH)
        self._methods = dbus.Interface(self._proxy, self.DBUS_PLAYER_NAME)
        self._properties = dbus.Interface(self._proxy, 'org.freedesktop.DBus.Properties')

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

    def fetch_properties(self) -> PlayerProperties:
        playback_status = self._properties.Get(self.DBUS_PLAYER_NAME, 'PlaybackStatus')
        metadata = self._properties.Get(self.DBUS_PLAYER_NAME, 'Metadata')

        return self._create_player_properties(playback_status, metadata)

    def on_properties_changed(self, callback: callable) -> None:
        self._proxy.connect_to_signal("PropertiesChanged", self._on_properties_changed_wrapper(callback))

    def _on_properties_changed_wrapper(self, callback: callable) -> callable:
        def handler(sender, props, extra) -> None:
            callback(self._create_player_properties(props['PlaybackStatus'], props['Metadata']))

        return handler

    @staticmethod
    def _create_player_properties(playback_status, metadata) -> PlayerProperties:
        return PlayerProperties(
            playback_status,
            metadata['xesam:artist'][0],
            metadata['xesam:albumArtist'][0],
            metadata['xesam:album'],
            metadata['xesam:title'],
            metadata['xesam:trackNumber']
        )
