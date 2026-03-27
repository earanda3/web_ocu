"""Ona Triangular - X:freq Y:velocitat Z:amplitud"""
import time, math
from modes.base_mode import BaseMode

class ModeOnaTriangular(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Triangular"
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

        # X = freqüència de l'ona (0.2 - 8 Hz)
        freq = 0.2 + (x / 127.0) * 7.8
        self.phase = (self.phase + dt * freq) % 1.0

        # Ona triangular: puja linealment fins a 0.5, baixa fins a 1.0
        tri = 1.0 - abs(self.phase * 2.0 - 1.0)

        # Z = rang de notes (amplitud de l'ona)
        span = 12 + int((z / 127.0) * 48)  # 1 a 5 octaves
        base = 36 + int((1.0 - z / 127.0) * 36)

        note = base + int(tri * span)
        note = max(0, min(127, note))

        # Y = velocitat
        vel = 40 + int((y / 127.0) * 87)

        if self.cur != note:
            if self.cur is not None:
                self.midi_out.send(self.note_off(self.cur, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.cur = note

        return {'note': note, 'phase': round(self.phase, 2)}

    def cleanup(self):
        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
            self.cur = None
        return []
