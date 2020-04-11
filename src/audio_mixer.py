import pulsectl
import threading


class AudioMixer:
    _volume_change_callback = None
    _volume_change_callback_lock = threading.RLock()

    def __init__(self) -> None:
        self._pulse = pulsectl.Pulse('midi-dbus-controller')

        self._thread = threading.Thread(target=self._run)
        self._running = True
        self._thread.start()

    def _run(self):
        pulse = pulsectl.Pulse('midi-dbus-controller')

        pulse.event_callback_set(self._event_callback)
        pulse.event_mask_set('sink')

        while self._running:
            pulse.event_listen(timeout=0.1)
            pass

    def _event_callback(self, event):
        self._on_volume_change()

    def stop(self):
        self._running = False

    def volume(self) -> int:
        sink = self._pulse.sink_list()[0]
        return self._pulse.volume_get_all_chans(sink)

    def set_volume(self, volume: float) -> None:
        if volume > 1:
            raise Exception('Volume should not be higher than 1.0')

        sink = self._pulse.sink_list()[0]
        self._pulse.volume_set_all_chans(sink, volume)

    def set_callback(self, callback: callable) -> None:
        with self._volume_change_callback_lock:
            self._volume_change_callback = callback

    def _on_volume_change(self):
        with self._volume_change_callback_lock:
            if self._volume_change_callback is not None:
                self._volume_change_callback(self.volume())
