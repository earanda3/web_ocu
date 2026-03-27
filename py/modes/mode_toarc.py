"""
Mode ToArc - Drone amb ale d'arquet automatic, familia de ToDrone
X: Velocitat del cicle d'arc (rapid 0.5s <-> lent 6s per cicle)
Y: Modulacio (CC1) - igual que al mode teclat i ToDrone
Z: Octava (2-5)
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = ( 0,   1,   2,   3,   4,  5,   6,   7,   8,   9,  10,  11)

# Intervals harmonics des de la tonica (semitones)
_HARMONICS = (
    (0,),            # Solo  : nota sola, pur
    (0, 7),          # 5a    : tonica + quinta (oberta)
    (0, 12),         # Oct   : tonica + octava (plena)
    (0, 7, 12),      # 5a+Oct: tonica + quinta + octava (classic)
    (0, 12, 19),     # Oct+5a: tonica + oct + quinta sup (rica)
    (0, 7, 12, 19),  # Stack : tonica + 5a + oct + 5a sup (maxim)
)
_HNAMES = ('Solo', '5a', 'Oct', '5a+Oct', 'Oct+5a', 'Stack')


def _on(midi_out, note, vel):
    try:
        msg = NoteOn(note & 0x7F, max(1, min(127, vel)))
        msg.channel = 0
        midi_out.send(msg)
    except Exception:
        pass


def _off(midi_out, note):
    try:
        msg = NoteOff(note & 0x7F, 0)
        msg.channel = 0
        midi_out.send(msg)
    except Exception:
        pass


def _cc(midi_out, cc, val):
    try:
        msg = ControlChange(cc, max(0, min(127, val)))
        msg.channel = 0
        midi_out.send(msg)
    except Exception:
        pass


class ModeToArc(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "ToArc"

        self.key_idx  = 0
        self.octave   = 3
        self.harm_idx = 0

        # Notes actives
        self.active       = []
        self.active_notes = []

        # Cicle d'arc (triangle wave sobre CC11)
        self.cycle_dur  = 2.0   # durada del cicle complet (s)
        self.phase      = 0.0   # posicio dins el cicle [0.0 - 1.0)
        self.last_t     = 0.0
        self.last_cc11  = -1    # valor CC11 anterior (evita enviar duplicats)

        # CC tracking
        self.cc_values = {1: 0, 11: 0}

        # Doble click
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.dbl_thr      = 0.4


    def _send_cc(self, cc_num, value):
        """Envia CC MIDI a tots els canals (igual que ToDrone)"""
        self.cc_values[cc_num] = max(0, min(127, value))
        try:
            for ch in range(16):
                midi_msg = ControlChange(cc_num, self.cc_values[cc_num], channel=ch)
                self.midi_out.send(midi_msg)
        except Exception:
            pass

    def _root(self):
        return self.octave * 12 + _OFF[self.key_idx]

    def _start_notes(self):
        self._stop_notes()
        root = self._root()
        for iv in _HARMONICS[self.harm_idx]:
            note = max(24, min(96, root + iv))
            _on(self.midi_out, note, 80)
            self.active.append(note)
        self.active_notes = list(self.active)

    def _stop_notes(self):
        for n in self.active:
            _off(self.midi_out, n)
        self.active       = []
        self.active_notes = []

    @staticmethod
    def _triangle(phase):
        """Triangle wave: 0->127 en 1a meitat, 127->0 en 2a meitat."""
        if phase < 0.5:
            return int(phase * 2.0 * 127)
        else:
            return int((1.0 - phase) * 2.0 * 127)

    def setup(self):
        self.initialized  = True
        self.phase        = 0.0
        self.last_t       = time.monotonic()
        self.last_cc11    = -1
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        _cc(self.midi_out, 11, 0)   # Silenci inicial
        _cc(self.midi_out, 64, 0)   # Sustain off
        self._start_notes()
        print(f"ToArc: {_KEYS[self.key_idx]} {_HNAMES[self.harm_idx]} oct{self.octave}")

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()
        dt  = now - self.last_t
        self.last_t = now

        # X: Velocitat del cicle (0.5s - 6s per cicle complet)
        self.cycle_dur = 0.5 + (1.0 - x / 127.0) * 5.5

        # Y: Modulacio (CC1) - igual que al mode teclat i ToDrone
        self._send_cc(1, y)

        # Z: Octava (2-5)
        new_oct = 2 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct
            _cc(self.midi_out, 11, 0)
            self._start_notes()
            print(f"ToArc: oct{self.octave}")

        # Avancar la fase del cicle d'arc
        self.phase = (self.phase + dt / self.cycle_dur) % 1.0

        # Aplicar CC11 com a envelope d'arc (solo actualitzar si canvia >= 1)
        cc11_val = self._triangle(self.phase)
        if abs(cc11_val - self.last_cc11) >= 1:
            _cc(self.midi_out, 11, cc11_val)
            self.last_cc11 = cc11_val

        # Doble click: canvi de tonalitat
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    _cc(self.midi_out, 11, 0)
                    self._start_notes()
                    self.phase = 0.0
                    print(f"ToArc: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {
            'key':   _KEYS[self.key_idx],
            'harm':  _HNAMES[self.harm_idx],
            'oct':   self.octave,
            'phase': round(self.phase, 2),
        }

    def stop(self):
        self.cleanup()

    def cleanup(self):
        _cc(self.midi_out, 11, 0)
        self._stop_notes()
        _cc(self.midi_out, 123, 0)
        _cc(self.midi_out, 120, 0)
        _cc(self.midi_out, 11, 127)
