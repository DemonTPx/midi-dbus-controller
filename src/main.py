import mido
import dbus
import signal
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from midi_controller import MidiController
from dbus_media_player_monitor import DbusMediaPlayerMonitor
from audio_mixer import AudioMixer
from event_handler import EventHandler

mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')

controller = MidiController('X-Touch One')
controller.reset()

dbus_loop = DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus(mainloop=dbus_loop)
monitor = DbusMediaPlayerMonitor(session_bus)

mixer = AudioMixer()

handler = EventHandler(controller, monitor, mixer)
handler.setup()

loop = GLib.MainLoop()


def sigint_handler(sig, frame):
    if sig == signal.SIGINT:
        loop.quit()


signal.signal(signal.SIGINT, sigint_handler)
loop.run()

handler.stop()
mixer.stop()
controller.reset()
