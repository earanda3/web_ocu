"""
Mode ToAcord - Drone d'acord continu, familia de ToDrone
X: Tipus d'acord (Major, Menor, Dom7, Maj7, Sus2, Sus4, Dim)
Y: Modulacio (CC1) - igual que al mode teclat
Z: Octavador
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# 7 tipus d'acord: (intervals des de la tonica)
_CHORDS = (
    (0, 4, 7),        # Major: brillant
    (0, 3, 7),        # Menor: melancolit
    (0, 4, 7, 10),    # Dom7: tensio, blues
    (0, 4, 7, 11),    # Maj7: modern, jazz
    (0, 2, 7),        # Sus2: obert, ambient
    (0, 5, 7),        # Sus4: suspens
    (0, 3, 6),        # Dim: fosc, inquietant
)
_CNAMES = ('Maj', 'Min', 'Dom7', 'Maj7', 'Sus2', 'Sus4', 'Dim')

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

class ModeToAcord(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "ToAcord"
        self.key_idx = 0
        self.octave = 3
        self.chord_idx = 0
        self.active_notes = []
        # CC tracking
        self.cc_values = {1: 0, 11: 127}
        # Doble click
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.dbl_thr = 0.4

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self._start_chord()

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, v):
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _send_cc(self, cc_num, value):
        """Envia CC MIDI a tots els canals (igual que ToDrone)"""
        self.cc_values[cc_num] = max(0, min(127, value))
        try:
            for ch in range(16):
                self.midi_out.send(ControlChange(cc_num, self.cc_values[cc_num], channel=ch))
        except Exception:
            pass

    def _stop_chord(self):
        for n in self.active_notes:
            self.midi_out.send(self.note_off(n, 0))
        self.active_notes = []

    def _start_chord(self):
        self._stop_chord()
        root = self._root()
        intervals = _CHORDS[self.chord_idx]
        vel = 85
        for iv in intervals:
            note = max(24, min(96, root + iv))
            self.active_notes.append(note)
            self.midi_out.send(self.note_on(note, vel))
        self._cc(11, 127)  # Expression al maxim
        print(f"ToAcord: {_KEYS[self.key_idx]}{_CNAMES[self.chord_idx]} oct{self.octave}")

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # POT X: Tipus d'acord (7 acords)
        new_chord = min(6, int((x / 127.0) * 7))
        if new_chord != self.chord_idx:
            self.chord_idx = new_chord
            self._start_chord()

        # POT Y: Modulacio (CC1) - igual que al mode teclat i ToDrone
        self._send_cc(1, y)

        # POT Z: Octava (2-5)
        new_oct = 2 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct
            self._start_chord()

        # Doble click: canviar tonalitat
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self._start_chord()
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {
            'key': _KEYS[self.key_idx],
            'chord': _CNAMES[self.chord_idx],
            'oct': self.octave,
        }

    def cleanup(self):
        self._stop_chord()
        self._cc(11, 127)
        self._cc(64, 0)
        self._cc(123, 0)
        self._cc(120, 0)
