"""Ona Dent de Serra - X:freq Y:nota base Z:velocitat"""
import time
from modes.base_mode import BaseMode

class ModeOnaSerra(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Serra"
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

        # X = freqüència de sweeping (0.1 - 6 Hz)
        freq = 0.1 + (x / 127.0) * 5.9
        self.phase = (self.phase + dt * freq) % 1.0

        # Ona dent de serra: puja linealment de 0 a 1 i torba al principi bruscament
        saw = self.phase  # 0.0 a 1.0

        # Y = nota base (nota MIDI 24-84)
        base = 24 + int((y / 127.0) * 60)

        # Sweeping d'una octava i mitja cap amunt
        span = 18
        note = base + int(saw * span)
        note = max(0, min(127, note))

        # Z = velocitat
        vel = 30 + int((z / 127.0) * 97)

        if self.cur != note:
            if self.cur is not None:
                self.midi_out.send(self.note_off(self.cur, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.cur = note

        return {'note': note, 'saw': round(saw, 2)}

    def cleanup(self):
        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
            self.cur = None
        return []
