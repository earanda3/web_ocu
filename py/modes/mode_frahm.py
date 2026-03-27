"""
Mode Frahm - Minimalisme piano modern, estil Nils Frahm
X: Velocitat
Y: Figura (Says, AllMelody, Forest, Spaces, Toilet)
Z: Octava
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# Frahm: mes rítmic i impulsius que Einaudi, pero igual de líric
_PATTERNS = (
    # Says: arpegi rapid repetitiu, hipnòtic - la seva obra mes icònica
    (0, 4, 7, 12, 7, 4, 0, 4, 7, 12, 14, 12),
    # All Melody: arc melòdic ampli, emotiu
    (0, 2, 5, 9, 12, 14, 12, 9, 7, 5, 2, 0),
    # My Friend the Forest: lent, natural, contemplador
    (0, 5, 7, 5, 0, 2, 4, 5, 7, 9, 7, 5),
    # Spaces: obert, expansiu, notes escasses
    (0, 7, 12, 0, 5, 7, 0, 4, 7, 0, 9, 12),
    # Toilet Brushes: traviès, bouncy, octaves
    (0, 12, 7, 12, 4, 12, 7, 12, 0, 12, 5, 12),
)
_PNAMES = ('Says', 'AllMelody', 'Forest', 'Spaces', 'Toilet')

# Frahm: velocitats mes dinàmiques (contrasts fort/fluix)
_VELS = (85, 60, 95, 55, 80, 50, 90, 55, 75, 50, 85, 60)

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeFrahm(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Frahm"
        self.key_idx     = 0
        self.octave      = 4
        self.pat_idx     = 0
        self.step        = 0
        self.last_note   = -1
        self.next_note_t = 0.0
        self.speed       = 0.22
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.dbl_thr      = 0.4

    def setup(self):
        self.initialized  = True
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.next_note_t  = time.monotonic()
        self.step = 0
        # Frahm: so net (poc sustain) + mica de reverb
        self._cc(64, 30)
        self._cc(91, 40)
        print(f"Frahm: {_PNAMES[self.pat_idx]} {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, val):
        try:
            self.midi_out.send(ControlChange(cc, max(0, min(127, val))))
        except Exception:
            pass

    def _play_step(self):
        pat  = _PATTERNS[self.pat_idx]
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

        # X: Velocitat (0.9s lent → 0.07s rapid — Frahm pot ser molt rapid)
        self.speed = max(0.07, 0.9 - (x / 127.0) * 0.83)

        # Y: Figura
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

        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self.step = 0
                    print(f"Frahm: {_KEYS[self.key_idx]}")
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
