"""Ona Quadrada - X:freq Y:velocitat Z:ample polsació"""
import time
from modes.base_mode import BaseMode

class ModeOnaQuadrada(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Quadrada"
        self.phase = 0.0
        self.t = time.monotonic()
        self.cur = None

    def setup(self):
        self.initialized = True
        self.phase = 0.0
        self.t = time.monotonic()
        self.cur = None

    def update(self, pot_values, button_states):
        now = time.monotonic()
        dt = now - self.t
        self.t = now
        x, y, z = pot_values

        # X = freqüència (0.3 - 10 Hz)
        freq = 0.3 + (x / 127.0) * 9.7
        self.phase = (self.phase + dt * freq) % 1.0

        # Z = duty cycle (ample del pols: 0.1 - 0.9)
        duty = 0.1 + (z / 127.0) * 0.8

        # Ona quadrada: HIGH si phase < duty, LOW altrament
        # HIGH = nota aguda, LOW = nota greu
        high = self.phase < duty
        note = 72 if high else 48  # C5 o C3

        # Afegir harmònic basat en Y
        note += int((y / 127.0) * 12)
        note = max(0, min(127, note))

        vel = 60 + int((y / 127.0) * 67)

        if self.cur != note:
            if self.cur is not None:
                self.midi_out.send(self.note_off(self.cur, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.cur = note

        return {'note': note, 'duty': round(duty, 2)}

    def cleanup(self):
        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
            self.cur = None
        return []
