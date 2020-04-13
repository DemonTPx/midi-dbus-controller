import mido
import dbus
import signal
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from midi_controller import MidiController
from dbus_media_player import DbusMediaPlayer
from audio_mixer import AudioMixer
from event_handler import EventHandler

mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')

controller = MidiController('X-Touch One:X-Touch One MIDI 1 24:0')
controller.reset()

dbus_loop = DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus(mainloop=dbus_loop)

player = DbusMediaPlayer(session_bus, 'spotify')

mixer = AudioMixer()

handler = EventHandler(controller, player, mixer)
handler.setup()

loop = GLib.MainLoop()


def sigint_handler(sig, frame):
    if sig == signal.SIGINT:
        loop.quit()
        handler.stop()
        mixer.stop()


signal.signal(signal.SIGINT, sigint_handler)
loop.run()

controller.reset()
