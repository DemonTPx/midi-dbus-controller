import mido
from lcd_7bit_font import lcd_7bit_render
from unidecode import unidecode
from typing import List


class MidiController:
    def __init__(self, name: str) -> None:
        self._name = name
        self._port_out = mido.open_output(name)

    def open_input(self, callback: callable):
        return mido.open_input(self._name, callback=callback)

    def reset(self) -> None:
        for n in range(1, 35):
            self.note_on(n, 0)

        self.control_change(70, 0)
        self.control_change(80, 64)
        self.control_change(90, 0)

        self.sysex(self.create_segment_display_data(''))
        self.sysex(self.create_lcd_display_data('', 0x0f))

    def note_on(self, note: int, velocity: int) -> None:
        self._send(mido.Message('note_on', note=note, velocity=velocity))

    def note_off(self, note: int, velocity: int) -> None:
        self._send(mido.Message('note_off', note=note, velocity=velocity))

    def control_change(self, control: int, value: int) -> None:
        self._send(mido.Message('control_change', control=control, value=value))

    def sysex(self, data: List[int]) -> None:
        self._send(mido.Message('sysex', data=data))

    def _send(self, message: mido.Message) -> None:
        self._port_out.send(message)

    def create_lcd_display_data(self, characters: str, cc: int) -> List[int]:
        characters = unidecode(characters)
        character_data = self._pad_to(list(map(ord, characters[:14])), 14)

        return [0x00, 0x20, 0x32, 0x41, 0x4c, 0x00, cc] + character_data

    def create_segment_display_data(self, characters: str) -> List[int]:
        characters = unidecode(characters)
        character_data = self._pad_to(lcd_7bit_render(characters[:12]), 12)

        return [0x00, 0x20, 0x32, 0x41, 0x37] + character_data + [0x00, 0x00]

    @staticmethod
    def _pad_to(data: List[int], n: int) -> List[int]:
        trimmed = data[:n]
        return trimmed + [0] * (n - len(trimmed))
