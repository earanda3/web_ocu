"""
Mode Arnalds - Contemplacio islandesa, estil Olafur Arnalds
X: Velocitat (molt lent per defecte)
Y: Figura (NearLight, Brot, Saman, Near, Drift)
Z: Octava
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# Arnalds: mes contemplatius, intervals mes amplis, sonoritat mes etèria
# Molts silencis implícits (interval=0 es nota molt fluixa)
_PATTERNS = (
    # Near Light: ascens lent i pausat, el mes famós
    (0, 4, 7, 9, 12, 9, 7, 4, 2, 0, 2, 4),
    # Brot (fragment): discontinu, fragmentat com el nom indica
    (0, 0, 7, 0, 12, 0, 5, 0, 9, 0, 7, 0),
    # Saman (junts): dues notes pròximes que es troben
    (0, 2, 4, 2, 0, 4, 7, 4, 2, 0, 5, 7),
    # Near (variant): igual de suau pero mes modal
    (0, 3, 7, 10, 12, 10, 7, 3, 0, 3, 5, 7),
    # Drift (deriva): les notes deriven amunt sense tornar
    (0, 2, 5, 7, 9, 12, 14, 12, 9, 7, 5, 2),
)
_PNAMES = ('NearLight', 'Brot', 'Saman', 'Near', 'Drift')

# Arnalds: molt suau, dinàmica comprimida, quasi tot piano
_VELS = (60, 45, 65, 40, 60, 40, 55, 40, 60, 40, 55, 45)

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModeArnalds(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Arnalds"
        self.key_idx     = 0
        self.octave      = 4
        self.pat_idx     = 0
        self.step        = 0
        self.last_note   = -1
        self.next_note_t = 0.0
        self.speed       = 0.7   # molt lent per defecte
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.dbl_thr      = 0.4

    def setup(self):
        self.initialized  = True
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.next_note_t  = time.monotonic()
        self.step = 0
        # Arnalds: molt de reverb i sustain — el so és atmosfèric
        self._cc(91, 70)   # Reverb abundant
        self._cc(64, 90)   # Sustain generós (notes es fonen)
        self._cc(1, 20)    # Modulació mínima per color
        print(f"Arnalds: {_PNAMES[self.pat_idx]} {_KEYS[self.key_idx]}")

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, val):
        try:
            self.midi_out.send(ControlChange(cc, max(0, min(127, val))))
        except Exception:
            pass

    def _play_step(self):
        pat  = _PATTERNS[self.pat_idx]
        interval = pat[self.step % len(pat)]
        note = max(24, min(108, self._root() + interval))
        # interval=0 primer pas: fort; repetit: molt fluix (silenci Arnalds)
        base_vel = _VELS[self.step % len(_VELS)]
        # Si el pas és 0 i no és el primer del patró: molt fluix
        vel = base_vel if interval != 0 or self.step % len(pat) == 0 else 20

        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        self.step = (self.step + 1) % len(pat)

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # X: Velocitat (2s molt lent → 0.2s moderat — mai arriba a ser rapid)
        self.speed = max(0.2, 2.0 - (x / 127.0) * 1.8)

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
                    print(f"Arnalds: {_KEYS[self.key_idx]}")
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
        self._cc(1, 0)
        self._cc(123, 0)
        self._cc(120, 0)
