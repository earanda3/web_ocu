"""Brasa - Foc i brases crepitants. X:flama Y:brasa Z:espurna"""
import time, random
from modes.base_mode import BaseMode

class ModeBrasa(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Brasa"
        self.t = time.monotonic()
        self.ember = 0.5   # estat brasa (0-1)
        self.flame = 0.0   # estat flama

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.ember = 0.5
        self.flame = 0.0

    def update(self, pot_values, button_states):
        now = time.monotonic()
        dt = min(now - self.t, 0.1)
        self.t = now
        x, y, z = pot_values

        # X = intensitat de la flama (moviment ràpid i irregular alt)
        flame_power = x / 127.0
        # Flama oscil·la caòticament
        self.flame += (random.random() - 0.45) * flame_power * 4 * dt
        self.flame = max(0.0, min(1.0, self.flame))

        # Y = temperatura brasa (notes de fons baixes i calentes)
        ember_temp = y / 127.0
        # Brasa decau lentament, s'activa amb petits espurnes
        self.ember += (random.random() - 0.5) * 0.05
        self.ember = max(0.3 * ember_temp, min(1.0, self.ember))

        # Z = espurnes (petits cracks ocasionals aguts)
        spark_prob = (z / 127.0) * 0.15

        # Nota de brasa (greu, lenta)
        if random.random() < 0.25:
            b_note = 28 + int(self.ember * 20)
            b_vel = int(self.ember * 70)
            if b_vel > 5:
                self.midi_out.send(self.note_on(b_note, b_vel))
                self.midi_out.send(self.note_off(b_note, 0))

        # Nota de flama (mig)
        if self.flame > 0.3 and random.random() < 0.4:
            f_note = 52 + int(self.flame * 24)
            f_vel = int(self.flame * 80)
            self.midi_out.send(self.note_on(f_note, f_vel))
            self.midi_out.send(self.note_off(f_note, 0))

        # Espurna (agut, curt, imprevisible)
        if random.random() < spark_prob:
            s_note = 84 + random.randint(0, 12)
            s_vel = random.randint(40, 110)
            self.midi_out.send(self.note_on(s_note, s_vel))
            self.midi_out.send(self.note_off(s_note, 0))

        return {'flame': round(self.flame, 2), 'ember': round(self.ember, 2)}

    def cleanup(self):
        return []
