"""
Mode Debussy - Impressionisme musical estil Debussy
X: Velocitat  Y: Patro melodic  Z: Octavador
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PATTERNS = (
    (0, 4, 7, 11, 7, 4, 2, 0),  # Clair de Lune: arpegi major7, somniat
    (0, 2, 4, 6, 8, 6, 4, 2),   # La Mer: escala de tons sencers, onadejant
    (0, 4, 7, 9, 7, 4, 0, 9),   # Arabesque: pentatonica, delicada
    (0, 2, 4, 7, 9, 7, 4, 2),   # Preludi (Faune): pentatonica, sensual
    (0, 3, 5, 7, 5, 3, 7, 0),   # Golliwog: blues, sincopat, ludic
)

# Debussy: suau, atmosferic, notes llargues i difoses
_VELS = (65, 55, 70, 50, 60, 52, 63, 48)

_KEYS = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

class ModeDebussy(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Debussy"
        self.key_idx = 0
        self.octave = 4
        self.pat_idx = 0
        self.step = 0
        self.last_note = -1
        self.next_note_time = 0.0
        self.speed = 0.55  # Debussy: lent i fluix per defecte
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.dbl_thr = 0.4
        # Fantasma: nota anterior continua sonat (sustain natural)
        self.ghost_note = -1
        self.ghost_time = 0.0
        self.ghost_on = False

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.next_note_time = time.monotonic()
        self.step = 0
        # Debussy viu en la reverberació: molta reverb i chorus
        self._cc(91, 110)  # Reverb: molt alta
        self._cc(93, 60)   # Chorus: moderada

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
        vel = max(15, min(127, int(_VELS[self.step % 8] * vel_scale)))

        # Impressionisme: la nota anterior s'esvaeix lentament (ghost)
        # No fem note_off immediat: la nota anterior perdura 80% del periode
        if self.ghost_on and self.ghost_note >= 0:
            self.midi_out.send(self.note_off(self.ghost_note, 0))
            self.ghost_on = False

        if self.last_note >= 0:
            # Programar esvaiment de l'actual com a ghost
            self.ghost_note = self.last_note
            self.ghost_on = True
            self.ghost_time = time.monotonic() + self.speed * 0.8

        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        self.step = (self.step + 1) % 8

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # Esvaiment de la nota fantasma
        if self.ghost_on and now >= self.ghost_time:
            self.midi_out.send(self.note_off(self.ghost_note, 0))
            self.ghost_on = False

        self.speed = 0.1 if x > 122 else (1.0 - (x / 127.0) * 0.9)

        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = 0

        new_oct = 3 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct

        if now >= self.next_note_time:
            self._play_step(0.7 + (y / 127.0) * 0.3)
            self.next_note_time = now + self.speed

        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self.step = 0
                    print(f"Debussy: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key_idx], 'oct': self.octave, 'pat': self.pat_idx}

    def cleanup(self):
        if self.ghost_on and self.ghost_note >= 0:
            self.midi_out.send(self.note_off(self.ghost_note, 0))
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._cc(91, 0)    # Reverb OFF
        self._cc(93, 0)    # Chorus OFF
        self._cc(64, 0)
        self._cc(123, 0)
        self._cc(120, 0)
