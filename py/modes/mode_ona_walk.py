"""Random Walk - Wandering melodic. X:velocitat Y:nota central Z:pas"""
import time, random
from modes.base_mode import BaseMode

class ModeOnaWalk(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Walk"
        self.pos = 60  # Nota actual (MIDI)
        self.t = time.monotonic()
        self.cur = None

    def setup(self):
        self.initialized = True
        self.pos = 60
        self.t = time.monotonic()
        self.cur = None

    def update(self, pot_values, button_states):
        now = time.monotonic()
        x, y, z = pot_values

        # X = velocitat de passos (0.1 - 4 passos/segon)
        rate = 0.1 + (x / 127.0) * 3.9
        interval = 1.0 / rate

        if now - self.t >= interval:
            self.t = now

            # Z = mida màxima del pas (1 - 7 semitons)
            step_size = 1 + int((z / 127.0) * 6)
            step = random.randint(-step_size, step_size)

            # Y = nota central atrau el walk cap a ella
            center = 24 + int((y / 127.0) * 72)
            drift = (center - self.pos) * 0.1
            self.pos = self.pos + step + drift

            # Clamp
            self.pos = max(24, min(96, int(self.pos)))
            note = self.pos
            vel = 50 + random.randint(-20, 40)
            vel = max(1, min(127, vel))

            if self.cur is not None:
                self.midi_out.send(self.note_off(self.cur, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.cur = note

        return {'note': self.cur, 'pos': self.pos}

    def cleanup(self):
        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
            self.cur = None
        return []
