"""
Mode Einaudi - Minimalisme emocionalment intens, estil Ludovico Einaudi
X: Velocitat (ràpid/lent)
Y: Figura melòdica (Nuvole, Experience, Una Mattina, River Flows, Primavera)
Z: Octava
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# 5 figures melòdiques — obertes, líriques, molt Einaudi
# Intervals sobre l'escala major/menor (semitones sobre tònica)
_PATTERNS = (
    # Nuvole Bianche: puja suaument, pausa, baixa
    (0, 4, 7, 12, 16, 12, 7, 4, 0, 4, 7, 4),
    # Experience: repetitiu hipnòtic, minimalista pur
    (0, 7, 12, 7, 0, 7, 12, 7, 0, 5, 9, 5),
    # Una Mattina: líric ascendent
    (0, 2, 4, 7, 9, 12, 9, 7, 4, 2, 0, 2),
    # River Flows: fluïd, ondulant
    (0, 4, 7, 11, 14, 11, 7, 4, 2, 4, 7, 9),
    # Primavera: viu, esperançador, major
    (0, 4, 7, 12, 7, 4, 5, 9, 12, 9, 5, 4),
)
_PNAMES = ('Nuvole', 'Experience', 'Mattina', 'River', 'Primavera')

_VELS = (75, 65, 80, 60, 85, 60, 75, 65, 70, 60, 75, 65)

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeEinaudi(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Einaudi"
        self.key_idx  = 0
        self.octave   = 4
        self.pat_idx  = 0
        self.step     = 0
        self.last_note = -1
        self.next_note_t = 0.0
        self.speed    = 0.35
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.dbl_thr      = 0.4

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.next_note_t  = time.monotonic()
        self.step = 0
        # Expressivitat: sustain suau + reverb lleuger
        self._cc(64, 70)
        self._cc(91, 30)
        print(f"Einaudi: {_PNAMES[self.pat_idx]} {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, val):
        try:
            self.midi_out.send(ControlChange(cc, max(0, min(127, val))))
        except Exception:
            pass

    def _play_step(self):
        pat = _PATTERNS[self.pat_idx]
        note = max(24, min(108, self._root() + pat[self.step % len(pat)]))
        vel  = _VELS[self.step % len(_VELS)]
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        self.step = (self.step + 1) % len(pat)

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # X: Velocitat (1.2s lent → 0.1s ràpid)
        self.speed = max(0.10, 1.2 - (x / 127.0) * 1.10)

        # Y: Figura melòdica
        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = 0

        # Z: Octava (3-6)
        new_oct = 3 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct

        if now >= self.next_note_t:
            self._play_step()
            self.next_note_t = now + self.speed

        # Doble click: tonalitat
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self.step = 0
                    print(f"Einaudi: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key_idx], 'pat': _PNAMES[self.pat_idx], 'oct': self.octave}

    def cleanup(self):
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._cc(64, 0)
        self._cc(91, 0)
        self._cc(123, 0)
        self._cc(120, 0)
