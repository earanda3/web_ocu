"""Estatic - Soroll estatic electrics. X:intensitat Y:to Z:burst"""
import time, random
from modes.base_mode import BaseMode

class ModeEstatic(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Estatic"
        self.t = time.monotonic()
        self.burst_left = 0
        self.burst_t = time.monotonic()

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.burst_left = 0

    def update(self, pot_values, button_states):
        now = time.monotonic()
        dt = now - self.t
        self.t = now
        x, y, z = pot_values

        # X = intensitat general de l'estàtic
        intensity = x / 127.0

        # Z = probabilitat de burst (ràfega de molts sorollets seguits)
        burst_prob = (z / 127.0) * 0.04  # fins a 4% cada update

        # Iniciar nou burst
        if self.burst_left <= 0 and random.random() < burst_prob:
            self.burst_left = random.randint(3, 12)

        fired = False
        if self.burst_left > 0 or random.random() < intensity * 0.3:
            # Y = freqüència del soroll (greu o agut)
            base = 48 + int((y / 127.0) * 60)
            note = base + random.randint(-12, 12)
            note = max(0, min(127, note))
            vel = random.randint(10, int(30 + intensity * 97))
            self.midi_out.send(self.note_on(note, vel))
            self.midi_out.send(self.note_off(note, 0))
            fired = True
            if self.burst_left > 0:
                self.burst_left -= 1

        return {'fired': fired, 'burst': self.burst_left}

    def cleanup(self):
        return []
