"""
Mode Chopin - Melodies romàntiques estil Chopin
X: Velocitat de la melodia
Y: Patró melòdic (nocturne, vals, mazurka, etude, balada)
Z: Octavador
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# Patrons melòdics (intervals relatius a la tònica, escala major/menor)
# 5 patrons, cada un amb 8 notes
_PATTERNS = (
    # Nocturne: líric, suau, dominant
    (0, 4, 7, 12, 7, 4, 2, 0),
    # Vals: 1-2-3 ritme de dansa
    (0, 7, 4, 7, 5, 7, 4, 2),
    # Mazurka: accent al 3r temps
    (0, 2, 4, 5, 7, 5, 4, 2),
    # Etude: escala ascendent-descendent
    (0, 2, 4, 5, 7, 9, 11, 12),
    # Balada: narrativa, dramàtica
    (0, 3, 7, 10, 12, 10, 7, 3),
)

# Velocitats per nota (expressivitat)
_VELS = (90, 70, 85, 65, 80, 65, 75, 60)

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_OFFSETS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

class ModeChopin(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Chopin"
        self.key_idx = 0
        self.octave = 4
        self.pat_idx = 0
        self.step = 0
        self.last_note = -1
        self.next_note_time = 0.0
        self.speed = 0.4  # segons entre notes

        # Doble click (igual que ToDrone)
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.dbl_thr = 0.4

        # Sustain per expressivitat Chopin
        self.sustain_on = False

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.next_note_time = time.monotonic()
        self.step = 0
        self._send_cc(64, 80)  # Sustain subtil
        self.sustain_on = True

    def _root(self):
        return self.octave * 12 + _OFFSETS[self.key_idx]

    def _send_cc(self, cc, val):
        try:
            self.midi_out.send(ControlChange(cc, val))
        except Exception:
            pass

    def _play_step(self, vel_scale):
        pat = _PATTERNS[self.pat_idx]
        interval = pat[self.step % len(pat)]
        note = max(24, min(108, self._root() + interval))
        base_vel = _VELS[self.step % len(_VELS)]
        vel = max(20, min(127, int(base_vel * vel_scale)))

        # Aturar nota anterior
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))

        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        self.step = (self.step + 1) % len(pat)

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # POT X: Velocitat (0.8s lent → 0.08s ràpid)
        if x < 5:
            self.speed = 0.8
        else:
            self.speed = 0.8 - (x / 127.0) * 0.72

        # POT Y: Patró melòdic (5 patrons)
        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = 0

        # POT Z: Octava (3-6)
        new_oct = 3 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct

        # Tocar nota si toca
        if now >= self.next_note_time:
            vel_scale = 0.5 + (y / 127.0) * 0.5  # expressivitat per Y
            self._play_step(vel_scale)
            self.next_note_time = now + self.speed

        # Doble click: canviar tonalitat
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    self.step = 0
                    print(f"Chopin: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key_idx], 'oct': self.octave, 'pat': self.pat_idx}

    def cleanup(self):
        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))
            self.last_note = -1
        self._send_cc(64, 0)   # Sustain OFF
        self._send_cc(123, 0)  # All Notes Off
        self._send_cc(120, 0)  # All Sound Off
        self.sustain_on = False
