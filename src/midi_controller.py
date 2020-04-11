import mido
from typing import List


class MidiController:
    letters = {
        "0": 0b0111111,
        "1": 0b0000110,
        "2": 0b1011011,
        "3": 0b1001111,
        "4": 0b1100110,
        "5": 0b1101101,
        "6": 0b1111101,
        "7": 0b0000111,
        "8": 0b1111111,
        "9": 0b1101111,
        "A": 0b1110111,
        "B": 0b1111111,
        "C": 0b1111111,
        "D": 0b0111111,
        "E": 0b1111001,
        "F": 0b1110001,
        "G": 0b0111101,
        "H": 0b1110110,
        "I": 0b0000110,
        "J": 0b0001110,
        "L": 0b0111000,
        "N": 0b0110111,
        "O": 0b0111111,
        "P": 0b1110011,
        "R": 0b1110111,
        "S": 0b1101101,
        "T": 0b1111000,
        "U": 0b0111110,
        "V": 0b0111110,
        "Y": 0b1101110,
        "Z": 0b1011011,
        ":": 0b0001001,
        "-": 0b1000000,
        ")": 0b0001111,
        "(": 0b0111001,
        " ": 0,
        "=": 0b1001001,
        "|": 0b0110110,
    }

    def __init__(self, name: str) -> None:
        self._name = name
        self._port_out = mido.open_output(name)

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

    def open_input(self, callback: callable):
        return mido.open_input(self._name, callback=callback)

    def create_lcd_display_data(self, characters: str, cc: int) -> List[int]:
        character_data = []
        for n in range(0, 14):
            if n < len(characters):
                character_data.append(ord(characters[n]))
            else:
                character_data.append(0)

        return [0x00, 0x20, 0x32, 0x41, 0x4c, 0x00, cc] + character_data

    def create_segment_display_data(self, characters: str) -> List[int]:
        if len(characters) > 12:
            raise

        character_data = []
        for n in range(0, 12):
            if n < len(characters):
                character_data.append(self.letters[characters[n]])
            else:
                character_data.append(0x00)

        return [0x00, 0x20, 0x32, 0x41, 0x37] + character_data + [0x00, 0x00]

    def _send(self, message: mido.Message) -> None:
        self._port_out.send(message)
