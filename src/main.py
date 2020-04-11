import mido
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from midi_controller import MidiController, Color, Invert
from dbus_media_player import DbusMediaPlayer, PlayerProperties
from audio_mixer import AudioMixer

mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')

controller = MidiController('X-Touch One:X-Touch One MIDI 1 24:0')
controller.reset()

dbus_loop = DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus(mainloop=dbus_loop)

player = DbusMediaPlayer(session_bus, 'spotify')

mixer = AudioMixer()


def properties_changed_handler(props: PlayerProperties):
    text = props.artist[0:7].ljust(7, ' ') + props.title[0:7].ljust(7, ' ')

    data = controller.create_lcd_display_data(text, Color.GREEN, Invert.NONE)
    controller.sysex(data)

    track = props.track_number
    text = '  SPOTIFY' + str(track).rjust(3, ' ')

    controller.sysex(controller.create_segment_display_data(text))

    if props.playback_status == 'Playing':
        controller.note_on(22, 0)
        controller.note_on(23, 127)

    if props.playback_status in ['Paused', 'Stopped']:
        controller.note_on(22, 127)
        controller.note_on(23, 0)


def handle_midi_message(message):
    if message.type == 'note_on' and message.velocity != 0:
        if message.note == 20:
            player.previous()
            player.play()
        if message.note == 21:
            player.next()
            player.play()
        if message.note == 22:
            player.stop()
        if message.note == 23:
            player.play_pause()

    if message.type == 'control_change':
        if message.control == 70:
            mixer.set_volume(int(message.value / 1.27))


controller.control_change(70, int(mixer.volume() * 1.27))
properties_changed_handler(player.fetch_properties())
player.on_properties_changed(properties_changed_handler)
controller.open_input(handle_midi_message)


loop = GLib.MainLoop()
loop.run()
