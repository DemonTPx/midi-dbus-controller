import alsaaudio


class AudioMixer:
    def __init__(self) -> None:
        self._mixer = alsaaudio.Mixer(alsaaudio.mixers()[0])

    def volume(self) -> int:
        return max(self._mixer.getvolume(alsaaudio.PCM_PLAYBACK))

    def set_volume(self, volume: int) -> None:
        self._mixer.setvolume(volume)
