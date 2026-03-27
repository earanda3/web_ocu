"""
Mode Mozart - Elegancia classica estil Mozart
X: Velocitat  Y: Patro melodic  Z: Octavador
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PATTERNS = (
    (0, 4, 7, 12, 7, 4, 0, 5),   # Eine Kleine: brillant, energica
    (0, 2, 3, 5, 7, 5, 3, 2),    # Alla Turca: marxa turca
    (0, 2, 3, 2, 0, 7, 5, 3),    # Simfonia 40: melancolica
    (0, 2, 4, 5, 7, 9, 7, 5),    # Sonata K545: escala elegant
    (0, 7, 5, 3, 2, 0, 3, 5),    # Don Giovanni: operistic
)

# Velocitats equilibrades - estil galant, sense sforzandos
_VELS = (85, 75, 88, 72, 82, 70, 80, 76)

_KEYS = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

class ModeMozart(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Mozart"
        self.key_idx = 0
        self.octave = 4
        self.pat_idx = 0
        self.step = 0
        self.last_note = -1
        self.next_note_time = 0.0
        self.speed = 0.25
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.dbl_thr = 0.4
        # Ornament: nota d'adorn cada 8 notes
        self.orn_count = 0
        self.orn_note = -1
        self.orn_time = 0.0
        self.orn_on = False

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.next_note_time = time.monotonic()
        self.step = self.orn_count = 0

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, v):
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _play_step(self, vel_scale):
        pat = _PATTERNS[self.pat_idx]
        note = max(24, min(108, self._root() + pat[self.step % 8]))
        vel = max(20, min(127, int(_VELS[self.step % 8] * vel_scale)))

        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))

        # Ornament mozartia cada 8 notes (nota +2 semitones, molt breu)
        self.orn_count = (self.orn_count + 1) % 8
        if self.orn_count == 0 and self.speed > 0.15:
            orn = min(108, note + 2)
            self.midi_out.send(self.note_on(orn, vel - 15))
            self.orn_note = orn
            self.orn_on = True
            self.orn_time = time.monotonic() + self.speed * 0.2

        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        self.step = (self.step + 1) % 8

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        if self.orn_on and now >= self.orn_time:
            self.midi_out.send(self.note_off(self.orn_note, 0))
            self.orn_on = False

        self.speed = 0.06 if x > 122 else (0.6 - (x / 127.0) * 0.54)

        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = self.orn_count = 0

        new_oct = 3 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct

        if now >= self.next_note_time:
            self._play_step(0.6 + (y / 127.0) * 0.4)
            self.next_note_time = now + self.speed

        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self.step = self.orn_count = 0
                    print(f"Mozart: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key_idx], 'oct': self.octave, 'pat': self.pat_idx}

    def cleanup(self):
        if self.orn_on and self.orn_note >= 0:
            self.midi_out.send(self.note_off(self.orn_note, 0))
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._cc(64, 0)
        self._cc(123, 0)
        self._cc(120, 0)
