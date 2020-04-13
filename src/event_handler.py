from audio_mixer import AudioMixer
from dbus_media_player_monitor import DbusMediaPlayerMonitor
from midi_controller import MidiController, Note, Control, Color, Invert
from dbus_media_player import DbusMediaPlayer, Track
from enum import Enum


class DisplayMethod(Enum):
    ARTIST_TITLE = 0
    ARTIST = 1
    TITLE = 2
    ALBUM = 3

    def next(self):
        return DisplayMethod((self.value + 1) % 4)


class EventHandler:
    _display_mode = DisplayMethod.ARTIST_TITLE
    _display_scroll = 0

    _player_color_map = {
        'spotify': Color.GREEN,
        'chrome': Color.YELLOW,
        'rhythmbox': Color.CYAN,
    }

    def __init__(self, controller: MidiController, monitor: DbusMediaPlayerMonitor, mixer: AudioMixer) -> None:
        self._controller = controller
        self._monitor = monitor
        self._mixer = mixer
        self._player = None
        self._midi_in_port = None
        self._track = None

    def setup(self):
        self.handle_volume(self._mixer.volume())
        self._mixer.set_callback(self.handle_volume)
        self._monitor.set_active_player_changed_callback(self.active_player_changed)
        self._player = self._monitor.get_active()
        self._init_player()
        self._midi_in_port = self._controller.open_input(self.handle_midi_message)

    def _init_player(self):
        if self._player:
            playback_status, track = self._player.fetch_properties()
            self.properties_changed_handler(playback_status, track)
            self._player.set_on_properties_changed_callback(self.properties_changed_handler)
        else:
            self.properties_changed_handler('None', Track.empty())

    def stop(self):
        if self._midi_in_port is not None:
            self._midi_in_port.close()

    def active_player_changed(self, player: DbusMediaPlayer) -> None:
        if self._player:
            self._player.set_on_properties_changed_callback(None)

        self._player = player
        self._init_player()

    def properties_changed_handler(self, playback_status: str, track: Track) -> None:
        if playback_status:
            if playback_status == 'None':
                self._controller.note_on(Note.STOP, 0)
                self._controller.note_on(Note.PLAY, 0)

            if playback_status == 'Playing':
                self._controller.note_on(Note.STOP, 0)
                self._controller.note_on(Note.PLAY, 127)

            if playback_status in ['Paused', 'Stopped']:
                self._controller.note_on(Note.STOP, 127)
                self._controller.note_on(Note.PLAY, 0)

        if track:
            if track.is_different_track(self._track):
                self._display_scroll = 0

            self._track = track

        self.update_display()

    def update_display(self) -> None:
        invert = Invert.NONE
        color = Color.BLACK
        if self._player:
            color = Color.WHITE
            if self._player.name_lower in self._player_color_map:
                color = self._player_color_map[self._player.name_lower]

        text = ' ' * 14
        if self._track is not None:
            s = self._display_scroll
            s7 = s + 7
            s14 = s + 14
            if self._display_mode == DisplayMethod.ARTIST_TITLE:
                text = self._track.artist[s:s7].ljust(7, ' ') + self._track.title[s:s7].ljust(7, ' ')
                invert = invert.TOP
            elif self._display_mode == DisplayMethod.ARTIST:
                text = self._track.artist[s:s14].ljust(14, ' ')
                invert = invert.BOTH
            elif self._display_mode == DisplayMethod.TITLE:
                text = self._track.title[s:s14].ljust(14, ' ')
            elif self._display_mode == DisplayMethod.ALBUM:
                text = self._track.album[s:s14].ljust(14, ' ')

        self._controller.sysex(self._controller.create_lcd_display_data(text, color, invert))

        track = self._track.track_number
        if track == 0:
            track = ''

        if self._player:
            text = '  ' + self._player.name[:7].ljust(7, ' ') + str(track).rjust(3, ' ')
        else:
            text = 'NoPlayer ' + str(track).rjust(3, ' ')

        self._controller.sysex(self._controller.create_segment_display_data(text))

    def handle_midi_message(self, message) -> None:
        if message.type == 'note_on' and message.velocity != 0:
            if message.note == Note.LED_KNOB.value:
                self._display_mode = self._display_mode.next()
                self._display_scroll = 0
                self.update_display()

            if self._player:
                if message.note == Note.PREVIOUS.value:
                    self._player.previous()
                    self._player.play()

                if message.note == Note.NEXT.value:
                    self._player.next()
                    self._player.play()

                if message.note == Note.STOP.value:
                    self._player.stop()

                if message.note == Note.PLAY.value:
                    self._player.play_pause()

            if message.note == Note.BANK_LEFT.value:
                self._monitor.select_previous_player()

            if message.note == Note.BANK_RIGHT.value:
                self._monitor.select_next_player()

            if message.note == Note.FADER.value:
                self._mixer.set_callback(None)

        if message.type == 'note_on' and message.velocity == 0:
            if message.note == Note.FADER.value:
                self._mixer.set_callback(self.handle_volume)

        if message.type == 'control_change':
            if message.control == Control.FADER.value:
                self._mixer.set_volume(message.value / 127)

            if message.control == Control.LED_RING.value:
                if message.value == 1:
                    self._display_scroll = min(self._display_scroll + 1, 100)
                    self.update_display()
                if message.value == 65:
                    self._display_scroll = max(self._display_scroll - 1, 0)
                    self.update_display()

    def handle_volume(self, volume: float) -> None:
        self._controller.control_change(Control.FADER, int(volume * 127))
