"""Pols - Polsadors independents per canal. X:bpm Y:nota Z:velocitat"""
import time
from modes.base_mode import BaseMode

class ModeOnaPols(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Pols"
        self.t = time.monotonic()
        self.on = False
        self.last_bpm = 0

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.on = False

    def update(self, pot_values, button_states):
        now = time.monotonic()
        x, y, z = pot_values

        # X = BPM (60 - 240)
        bpm = 60 + int((x / 127.0) * 180)
        period = 60.0 / bpm  # durada d'un beat
        half = period * 0.5  # nota sona la meitat del període

        elapsed = now - self.t

        if not self.on and elapsed >= period:
            # Temps de nova nota
            note = 36 + int((y / 127.0) * 60)
            note = max(0, min(127, note))
            vel = 40 + int((z / 127.0) * 87)
            self.midi_out.send(self.note_on(note, vel))
            self._note = note
            self.on = True
            self.t = now

        elif self.on and elapsed >= half:
            # Apagar nota
            if hasattr(self, '_note'):
                self.midi_out.send(self.note_off(self._note, 0))
            self.on = False

        return {'bpm': bpm, 'on': self.on}

    def cleanup(self):
        if self.on and hasattr(self, '_note'):
            self.midi_out.send(self.note_off(self._note, 0))
        return []
