"""Bit - Glitch de bits, petits errors digitals. X:rate Y:to Z:corruptio"""
import time, random
from modes.base_mode import BaseMode

class ModeBit(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Bit"
        self.t = time.monotonic()
        self.byte = 0b10110100  # Byte inicial "corromput"

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.byte = random.randint(0, 255)

    def update(self, pot_values, button_states):
        now = time.monotonic()
        x, y, z = pot_values

        # X = rate de glitch (1-30 glitches/segon)
        rate = 1 + (x / 127.0) * 29
        interval = 1.0 / rate

        if now - self.t >= interval:
            self.t = now

            # Z = corrupció: quants bits flipem (1-4 bits)
            bits_to_flip = 1 + int((z / 127.0) * 3)
            for _ in range(bits_to_flip):
                bit = 1 << random.randint(0, 7)
                self.byte ^= bit  # XOR per flipar bit
            self.byte &= 0xFF

            # Y = offset de to (greu o agut)
            base = 24 + int((y / 127.0) * 60)

            # La nota ve del byte corromput (escala al rang)
            note = base + int((self.byte / 255.0) * 36)
            note = max(0, min(127, note))

            # Velocitat: bits actius al byte = intensitat
            active_bits = bin(self.byte).count('1')
            vel = 15 + active_bits * 14  # 15-127

            self.midi_out.send(self.note_on(note, vel))
            self.midi_out.send(self.note_off(note, 0))

        return {'byte': bin(self.byte), 'val': self.byte}

    def cleanup(self):
        return []
