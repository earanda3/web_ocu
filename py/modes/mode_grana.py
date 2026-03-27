"""Grana - Granular crispy. X:velocitat Y:centre Z:dispersio"""
import time, random
from modes.base_mode import BaseMode

class ModeGrana(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Grana"
        self.t = time.monotonic()
        self.grains = []  # [(note, off_time)]

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.grains = []

    def update(self, pot_values, button_states):
        now = time.monotonic()
        x, y, z = pot_values

        # Apagar grans que han expirat
        still = []
        for (note, off_t) in self.grains:
            if now >= off_t:
                self.midi_out.send(self.note_off(note, 0))
            else:
                still.append((note, off_t))
        self.grains = still

        # X = rate de nous grans (1-20 grans/segon)
        rate = 1 + (x / 127.0) * 19
        interval = 1.0 / rate

        if now - self.t >= interval:
            self.t = now
            # Y = nota central del grain cloud
            center = 36 + int((y / 127.0) * 72)
            # Z = dispersió (quant s'allunya del centre)
            spread = int((z / 127.0) * 24)
            note = center + random.randint(-spread, spread)
            note = max(0, min(127, note))

            # Durada molt curta (grain): 20ms - 120ms
            dur = 0.02 + random.random() * 0.1
            vel = random.randint(30, 110)
            self.midi_out.send(self.note_on(note, vel))
            self.grains.append((note, now + dur))

        return {'grains': len(self.grains)}

    def cleanup(self):
        for (note, _) in self.grains:
            self.midi_out.send(self.note_off(note, 0))
        self.grains = []
        return []
