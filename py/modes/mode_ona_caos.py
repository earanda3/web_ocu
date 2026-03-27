"""Caos Logistic - Mapa logistic com a oscil·lador. X:r Y:base Z:vel"""
from modes.base_mode import BaseMode

class ModeOnaCaos(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Caos"
        self.x = 0.5  # Estat del mapa logístic
        self.cur = None

    def setup(self):
        self.initialized = True
        self.x = 0.5
        self.cur = None

    def update(self, pot_values, button_states):
        px, y, z = pot_values

        # X = paràmetre r del mapa logístic (3.5 - 4.0 = caos)
        r = 3.5 + (px / 127.0) * 0.5

        # Iterar el mapa logístic: x = r * x * (1 - x)
        self.x = r * self.x * (1.0 - self.x)
        val = max(0.0, min(1.0, self.x))

        # Y = nota base
        base = 24 + int((y / 127.0) * 60)

        # Mapejar valor caòtic a nota en el rang d'una octava
        note = base + int(val * 24)
        note = max(0, min(127, note))

        # Z = velocitat
        vel = 40 + int((z / 127.0) * 87)

        if self.cur != note:
            if self.cur is not None:
                self.midi_out.send(self.note_off(self.cur, 0))
            self.midi_out.send(self.note_on(note, vel))
            self.cur = note

        return {'note': note, 'chaos': round(self.x, 3)}

    def cleanup(self):
        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
            self.cur = None
        return []
