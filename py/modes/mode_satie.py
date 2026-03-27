"""
Mode Satie - Minimalisme hipnotic estil Erik Satie
X: Velocitat  Y: Patro melodic  Z: Octavador
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_PATTERNS = (
    (0, 4, 7, 11, 7, 4, 0, 7),  # Gymnopedie 1: vals lent, major7
    (0, 1, 5, 7, 1, 5, 7, 10),  # Gnossienne 1: modal, misterios
    (0, 3, 7, 10, 7, 3, 0, 5),  # Gymnopedie 2: melancolit, menor
    (0, 2, 5, 7, 5, 2, 0, 5),   # Gnossienne 3: doric, hipnotic
    (0, 0, 4, 4, 7, 7, 4, 0),   # Vexations: repetitiu, meditabund
)

# Satie: pianissimo absolut, quasi no hi ha variacio dinamica
_VELS = (52, 45, 55, 42, 50, 44, 53, 40)

_KEYS = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

class ModeSatie(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Satie"
        self.key_idx = 0
        self.octave = 4
        self.pat_idx = 0
        self.step = 0
        self.last_note = -1
        self.next_note_time = 0.0
        self.speed = 0.9   # Satie: molt lent per defecte
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.dbl_thr = 0.4
        # Silenci intencional: la nota s'atura al 60% del periode (Satie space)
        self.silence_time = 0.0
        self.silence_active = False

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.next_note_time = time.monotonic()
        self.step = 0
        self._cc(91, 90)   # Reverb suau
        self._cc(10, 64)   # Pan centrat

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
        vel = max(10, min(90, int(_VELS[self.step % 8] * vel_scale)))

        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.silence_active = False

        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        # Silenci satian: la nota s'apaga sola al 55% del periode
        self.silence_time = time.monotonic() + self.speed * 0.55
        self.silence_active = True
        self.step = (self.step + 1) % 8

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # Silenci intencional (l'espai es part de la musica)
        if self.silence_active and now >= self.silence_time:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.silence_active = False

        # POT X: Velocitat molt lenta (1.5s) a moderada (0.2s)
        self.speed = 0.2 if x > 122 else (1.5 - (x / 127.0) * 1.3)

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
                    print(f"Satie: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key_idx], 'oct': self.octave, 'pat': self.pat_idx}

    def cleanup(self):
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._cc(91, 0)
        self._cc(64, 0)
        self._cc(123, 0)
        self._cc(120, 0)
