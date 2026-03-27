"""
Mode Beethoven - Drama romàntic estil Beethoven
X: Velocitat de la melodia
Y: Patró melòdic (5a Simfonia, Moonlight, Oda Alegria, Per Elisa, Appassionata)
Z: Octavador
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# 5 patrons icònics de Beethoven (intervals relatius a la tònica)
_PATTERNS = (
    # 5a Simfonia: motiu del destí (curt-curt-curt-llarg) + eco
    (7, 7, 7, 3, 5, 5, 5, 0),
    # Moonlight Sonata: arpegi menor, líric i fosc
    (0, 3, 7, 12, 7, 3, 0, 3),
    # Oda a l'Alegria: ascendent jubilosa
    (0, 0, 2, 4, 4, 2, 0, 2),
    # Per Elisa: patró inconfusible
    (12, 11, 12, 11, 12, 7, 10, 9),
    # Appassionata: dramàtica, potent, amb octaves
    (0, 3, 7, 12, 10, 7, 3, 0),
)

# Velocitats que reflecteixen el caràcter dramàtic de Beethoven
# Fortes i pianos sobtats (sforzando)
_VELS = (110, 60, 105, 55, 115, 50, 100, 65)

_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_OFFSETS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

class ModeBeethoven(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Beethoven"
        self.key_idx = 0
        self.octave = 4
        self.pat_idx = 0
        self.step = 0
        self.last_note = -1
        self.next_note_time = 0.0
        self.speed = 0.35

        # Doble click (com ToDrone i Chopin)
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.dbl_thr = 0.4

        # Dinàmica: accent sforzando cada 4 notes (Beethoven!)
        self.sfz_counter = 0

    def setup(self):
        self.initialized = True
        self.last_release = [0.0] * 16
        self.last_btn = [False] * 16
        self.next_note_time = time.monotonic()
        self.step = 0
        self.sfz_counter = 0

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

        # Dinàmica beethoveniana: sforzando cada 4 notes
        base_vel = _VELS[self.step % len(_VELS)]
        if self.sfz_counter == 0:
            # Sforzando: accent brusc (+20)
            vel = min(127, int(base_vel * vel_scale) + 20)
        else:
            vel = max(20, int(base_vel * vel_scale))
        self.sfz_counter = (self.sfz_counter + 1) % 4

        if self.last_note >= 0:
            self.midi_out.send(self.note_off(self.last_note, 0))

        self.midi_out.send(self.note_on(note, vel))
        self.last_note = note
        self.step = (self.step + 1) % len(pat)

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # POT X: Velocitat (0.7s lent → 0.07s ràpid)
        self.speed = 0.07 if x > 122 else (0.7 - (x / 127.0) * 0.63)

        # POT Y: Patró melòdic (5 patrons)
        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = 0
            self.sfz_counter = 0

        # POT Z: Octava (3-6)
        new_oct = 3 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct

        # Tocar nota si toca
        if now >= self.next_note_time:
            # vel_scale: Y també controla intensitat dramàtica
            vel_scale = 0.55 + (y / 127.0) * 0.45
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
                    self.sfz_counter = 0
                    print(f"Beethoven: {_KEYS[self.key_idx]}")
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
