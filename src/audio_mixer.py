import gi
gi.require_version('Cvc', '1.0')

from gi.repository import Cvc


class AudioMixer:
    callback = None

    def __init__(self) -> None:
        self._controller = Cvc.MixerControl(name="bert")
        self._volume_max = self._controller.get_vol_max_norm()
        self._controller.connect('state-changed', self._on_state_changed)
        self._controller.open()

    def volume(self) -> int:
        return int(self._mixer_sink.get_volume() / self._volume_max * 100)

    def set_volume(self, volume: float) -> None:
        self._mixer_sink.props.volume = volume * self._volume_max
        self._mixer_sink.push_volume()

    def _on_state_changed(self, control, state):
        if state == Cvc.MixerControlState.READY:
            self._mixer_sink = control.get_default_sink()
            self._mixer_sink.connect('notify::volume', self._update_volume)
            print(self._mixer_sink.props.description)
            volume = self._mixer_sink.props.volume / self._volume_max
            self.callback(volume)

    def _update_volume(self, mixer_sink, *args):
        volume = mixer_sink.props.volume / self._volume_max
        if self.callback is not None:
            self.callback(volume)
