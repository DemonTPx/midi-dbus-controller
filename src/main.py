import mido
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from midi_controller import MidiController, Note, Control, Color, Invert
from dbus_media_player import DbusMediaPlayer, PlayerProperties
from audio_mixer import AudioMixer

mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')

controller = MidiController('X-Touch One:X-Touch One MIDI 1 24:0')
controller.reset()

dbus_loop = DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus(mainloop=dbus_loop)

player = DbusMediaPlayer(session_bus, 'spotify')

mixer = AudioMixer()


def properties_changed_handler(props: PlayerProperties) -> None:
    text = props.artist[0:7].ljust(7, ' ') + props.title[0:7].ljust(7, ' ')

    data = controller.create_lcd_display_data(text, Color.GREEN, Invert.NONE)
    controller.sysex(data)

    track = props.track_number
    text = '  SPOTIFY' + str(track).rjust(3, ' ')

    controller.sysex(controller.create_segment_display_data(text))

    if props.playback_status == 'Playing':
        controller.note_on(Note.STOP, 0)
        controller.note_on(Note.PLAY, 127)

    if props.playback_status in ['Paused', 'Stopped']:
        controller.note_on(Note.STOP, 127)
        controller.note_on(Note.PLAY, 0)


def handle_midi_message(message) -> None:
    if message.type == 'note_on' and message.velocity != 0:
        if message.note == Note.PREVIOUS.value:
            player.previous()
            player.play()

        if message.note == Note.NEXT.value:
            player.next()
            player.play()

        if message.note == Note.STOP.value:
            player.stop()

        if message.note == Note.PLAY.value:
            player.play_pause()

        if message.note == Note.FADER.value:
            mixer.callback = None

    if message.type == 'note_on' and message.velocity == 0:
        if message.note == Note.FADER.value:
            mixer.callback = handle_volume

    if message.type == 'control_change':
        if message.control == Control.FADER.value:
            mixer.set_volume(message.value / 127)


def handle_volume(volume: float) -> None:
    controller.control_change(Control.FADER, int(volume * 127))


handle_volume(mixer.volume())
mixer.callback = handle_volume
properties_changed_handler(player.fetch_properties())
player.on_properties_changed(properties_changed_handler)
controller.open_input(handle_midi_message)


loop = GLib.MainLoop()
loop.run()
