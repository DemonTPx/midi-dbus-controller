from audio_mixer import AudioMixer
from midi_controller import MidiController, Note, Control, Color, Invert
from dbus_media_player import DbusMediaPlayer, PlayerProperties
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

    def __init__(self, controller: MidiController, player: DbusMediaPlayer, mixer: AudioMixer) -> None:
        self._controller = controller
        self._player = player
        self._mixer = mixer
        self._midi_in_port = None
        self._props = None

    def setup(self):
        self.handle_volume(self._mixer.volume())
        self._mixer.set_callback(self.handle_volume)
        self.properties_changed_handler(self._player.fetch_properties())
        self._player.on_properties_changed(self.properties_changed_handler)
        self._midi_in_port = self._controller.open_input(self.handle_midi_message)

    def stop(self):
        if self._midi_in_port is not None:
            self._midi_in_port.close()

    def properties_changed_handler(self, props: PlayerProperties) -> None:
        if props.is_different_track(self._props):
            self._display_scroll = 0

        self._props = props

        if props.playback_status == 'Playing':
            self._controller.note_on(Note.STOP, 0)
            self._controller.note_on(Note.PLAY, 127)

        if props.playback_status in ['Paused', 'Stopped']:
            self._controller.note_on(Note.STOP, 127)
            self._controller.note_on(Note.PLAY, 0)

        self.update_display()

    def update_display(self) -> None:
        text = ' ' * 14
        if self._props is not None:
            s = self._display_scroll
            s7 = s + 7
            s14 = s + 14
            if self._display_mode == DisplayMethod.ARTIST_TITLE:
                text = self._props.artist[s:s7].ljust(7, ' ') + self._props.title[s:s7].ljust(7, ' ')
            elif self._display_mode == DisplayMethod.ARTIST:
                text = self._props.artist[s:s14].ljust(14, ' ')
            elif self._display_mode == DisplayMethod.TITLE:
                text = self._props.title[s:s14].ljust(14, ' ')
            elif self._display_mode == DisplayMethod.ALBUM:
                text = self._props.album[s:s14].ljust(14, ' ')

        data = self._controller.create_lcd_display_data(text, Color.GREEN, Invert.NONE)
        self._controller.sysex(data)

        track = self._props.track_number
        text = '  Spotify' + str(track).rjust(3, ' ')

        self._controller.sysex(self._controller.create_segment_display_data(text))

    def handle_midi_message(self, message) -> None:
        if message.type == 'note_on' and message.velocity != 0:
            if message.note == Note.LED_KNOB.value:
                self._display_mode = self._display_mode.next()
                self._display_scroll = 0
                self.update_display()

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
