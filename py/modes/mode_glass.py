"""
Mode Glass - Minimalisme repetitiu, estil Philip Glass
X: Velocitat del cicle (ràpid/lent)
Y: Motiu (Metamorphosis, Glassworks, Koyaanisqatsi, Mad Rush, Akhnaten)
Z: Octava + densitat harmònica
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# Motius de Philip Glass: patrons curts molt repetitius amb canvis de fase
# El secret de Glass: patrons de 4-6 notes que canvien lleument cada cop
_PATTERNS = (
    # Metamorphosis: tres notes ascendents, volta
    (0, 4, 7, 4, 0, 4, 7, 9, 7, 4),
    # Glassworks: cèl·lula mínima 1-2-3
    (0, 3, 7, 3, 0, 3, 5, 3, 0, 2),
    # Koyaanisqatsi: greu, hipnòtic, repetitiu absolut
    (0, 7, 12, 7, 0, 7, 5, 7, 0, 7),
    # Mad Rush: superposició de figures, dens
    (0, 4, 7, 11, 12, 11, 7, 4, 2, 0),
    # Akhnaten: arcaic, modal, quasi estàtic
    (0, 2, 5, 7, 9, 7, 5, 2, 0, 2),
)
_PNAMES = ('Metamorphosis', 'Glassworks', 'Koyaanisqatsi', 'MadRush', 'Akhnaten')

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeGlass(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Glass"
        self.key_idx   = 0
        self.octave    = 4
        self.pat_idx   = 0
        self.step      = 0
        self.last_note = -1
        # Glass: dues veus simultànies (tret característic del seu estil)
        self.harmony_note = -1
        self.next_note_t  = 0.0
        self.speed        = 0.18  # Glass és ràpid per defecte
        self.cycle_count  = 0     # comptador de cicles completats
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.dbl_thr      = 0.4

    def setup(self):
        self.initialized  = True
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.next_note_t  = time.monotonic()
        self.step = 0
        self.cycle_count = 0
        self._cc(64, 0)   # Glass: sense sustain, notes seques
        self._cc(91, 15)  # Reverb molt lleuger
        print(f"Glass: {_PNAMES[self.pat_idx]} {_KEYS[self.key_idx]}")

    def _root(self, oct_offset=0):
        return (self.octave + oct_offset) * 12 + _OFF[self.key_idx]

    def _cc(self, cc, val):
        try:
            self.midi_out.send(ControlChange(cc, max(0, min(127, val))))
        except Exception:
            pass

    def _play_step(self, density):
        pat  = _PATTERNS[self.pat_idx]
        idx  = self.step % len(pat)
        root = self._root()

        note = max(24, min(108, root + pat[idx]))
        vel  = 80 if idx % 2 == 0 else 65  # accent alt/baix, típic Glass

        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))

        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note

        # Segon veu: veu harmònica una octava avall (density > 0.4)
        if density > 0.4:
            harm = max(24, min(108, root - 12 + pat[(idx + len(pat)//2) % len(pat)]))
            if self.harmony_note >= 0:
                self.midi_out.send(self.note_off(self.harmony_note, 0))
            self.midi_out.send(self.note_on(harm, max(1, int(vel * 0.6))))
            self.harmony_note = harm
        elif self.harmony_note >= 0:
            self.midi_out.send(self.note_off(self.harmony_note, 0))
            self.harmony_note = -1

        self.step = (self.step + 1) % len(pat)
        if self.step == 0:
            self.cycle_count += 1

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # X: Velocitat (0.35s lent → 0.08s ràpid, Glass és intens)
        self.speed = max(0.08, 0.35 - (x / 127.0) * 0.27)

        # Y: Motiu melòdic
        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = 0
            self.cycle_count = 0

        # Z: Octava + densitat (si Z > 64 activa segon veu)
        new_oct = 3 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct
        density = z / 127.0

        if now >= self.next_note_t:
            self._play_step(density)
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
                    self.cycle_count = 0
                    print(f"Glass: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {
            'key':    _KEYS[self.key_idx],
            'motiu':  _PNAMES[self.pat_idx],
            'cicle':  self.cycle_count,
        }

    def cleanup(self):
        for n in (self.last_note, self.harmony_note):
            if n >= 0:
                try:
                    self.midi_out.send(self.note_off(n, 0))
                except Exception:
                    pass
        self.last_note = self.harmony_note = -1
        self._cc(91, 0)
        self._cc(123, 0)
        self._cc(120, 0)
