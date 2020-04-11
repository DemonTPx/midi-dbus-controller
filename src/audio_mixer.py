import pulsectl


class AudioMixer:
    def __init__(self) -> None:
        self._pulse = pulsectl.Pulse('midi-dbus-controller')
        self._sink = self._pulse.sink_list()[0]

    def volume(self) -> int:
        return self._pulse.volume_get_all_chans(self._sink)

    def set_volume(self, volume: float) -> None:
        if volume > 1:
            raise Exception('Volume should not be higher than 1.0')

        self._pulse.volume_set_all_chans(self._sink, volume)
