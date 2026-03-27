"""Crackle - Crepitació aleatoria de vinilo. X:densitat Y:to Z:volum"""
import time, random
from modes.base_mode import BaseMode

class ModeCrackle(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Crackle"
        self.t = time.monotonic()
        self.cooldown = 0.0

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.cooldown = 0.0

    def update(self, pot_values, button_states):
        now = time.monotonic()
        x, y, z = pot_values

        # X = densitat de crepitació (cops per segon: 1 - 40)
        density = 1 + (x / 127.0) * 39
        # Interval mig entre cops (amb variació aleatòria)
        mean_gap = 1.0 / density
        self.cooldown -= (now - self.t)
        self.t = now

        fired = False
        if self.cooldown <= 0:
            # Y = zona tonal del petardeig (agut/greu)
            base = 60 + int((y / 127.0) * 48)  # 60-108
            # Petardeig: nota curta molt aleatoria al voltant de base
            note = base + random.randint(-6, 6)
            note = max(0, min(127, note))

            # Z = volum / intensitat del petardeig
            vel_max = 20 + int((z / 127.0) * 107)
            vel = random.randint(vel_max // 3, vel_max)

            self.midi_out.send(self.note_on(note, vel))
            self.midi_out.send(self.note_off(note, 0))
            fired = True

            # Proper cop: interval aleatori al voltant de la densitat
            jitter = random.uniform(0.3, 1.7)
            self.cooldown = mean_gap * jitter

        return {'fired': fired, 'density': int(density)}

    def cleanup(self):
        return []
