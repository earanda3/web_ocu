"""
Mode Bach - Contrapunt barroc estil J.S. Bach
X: Velocitat  Y: Patro melodic  Z: Octavador
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PATTERNS = (
    (0, 4, 7, 12, 7, 4, 0, 4),   # Preludi BWV 846: arpegi del Clavecin
    (0, 3, 7, 10, 12, 10, 7, 3), # Toccata i Fuga Rem: drama d'orgue
    (0, 2, 4, 7, 9, 7, 4, 2),    # Air (Suite 3): lent i cantabile
    (0, 2, 4, 5, 7, 5, 4, 2),    # Invencio 1: contrapunt ascendent
    (0, 4, 7, 9, 7, 4, 2, 0),    # Jesu Joy: fluida, en tres
)

# Bach: dinàmiques barroques, igualades (no hi ha creixcuts romantics)
_VELS = (78, 72, 76, 70, 74, 72, 78, 68)

_KEYS = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

class ModeBach(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Bach"
        self.key_idx = 0
        self.octave = 4
        self.pat_idx = 0
        self.step = 0
        self.last_note = -1
        self.next_note_time = 0.0
        self.speed = 0.3
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.dbl_thr = 0.4
        # Contrapunt: segona veu a la quinta inferior cada 3 notes
        self.cpnt_note = -1
        self.cpnt_time = 0.0
        self.cpnt_on = False

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.next_note_time = time.monotonic()
        self.step = 0

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

        # Contrapunt barroc: cada 3 notes, segona veu a la quinta (−7 st)
        if self.step % 3 == 0:
            cv = max(24, note - 7)
            if self.cpnt_on and self.cpnt_note >= 0:
                self.midi_out.send(self.note_off(self.cpnt_note, 0))
            self.midi_out.send(self.note_on(cv, vel - 12))
            self.cpnt_note = cv
            self.cpnt_on = True
            self.cpnt_time = time.monotonic() + self.speed * 0.9

        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        self.step = (self.step + 1) % 8

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # Tancar veu de contrapunt
        if self.cpnt_on and now >= self.cpnt_time:
            self.midi_out.send(self.note_off(self.cpnt_note, 0))
            self.cpnt_on = False

        self.speed = 0.07 if x > 122 else (0.7 - (x / 127.0) * 0.63)

        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = 0

        new_oct = 3 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct

        if now >= self.next_note_time:
            self._play_step(0.65 + (y / 127.0) * 0.35)
            self.next_note_time = now + self.speed

        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self.step = 0
                    print(f"Bach: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key_idx], 'oct': self.octave, 'pat': self.pat_idx}

    def cleanup(self):
        if self.cpnt_on and self.cpnt_note >= 0:
            self.midi_out.send(self.note_off(self.cpnt_note, 0))
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._cc(64, 0)
        self._cc(123, 0)
        self._cc(120, 0)
