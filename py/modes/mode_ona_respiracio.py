"""Respiracio - Ona de respiracio lenta. X:ritme Y:nota Z:profunditat"""
import time, math
from modes.base_mode import BaseMode

class ModeOnaRespiracio(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Respiracio"
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

        # X = velocitat de respiració (0.05 - 0.5 Hz, respiracions lentes)
        freq = 0.05 + (x / 127.0) * 0.45
        self.phase = (self.phase + dt * freq) % 1.0

        # Subida suau (sin^2 per a forma de respiració natural)
        breath = math.sin(self.phase * math.pi) ** 2

        # Y = nota central
        base = 36 + int((y / 127.0) * 48)

        # Z = profunditat de la respiració (rang de notes)
        depth = int((z / 127.0) * 24)
        note = base + int(breath * depth)
        note = max(0, min(127, note))

        # Velocitat proporcional a la respiració (suau)
        vel = 20 + int(breath * 90)

        if self.cur != note:
            if self.cur is not None:
                self.midi_out.send(self.note_off(self.cur, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.cur = note

        return {'note': note, 'breath': round(breath, 2)}

    def cleanup(self):
        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
            self.cur = None
        return []
