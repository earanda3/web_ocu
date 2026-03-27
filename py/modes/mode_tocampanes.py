"""
Mode ToCampanes - Carilló de campanes aleatori, familia To
Notes aleatories d'una escala escollidaens intervals irregulars, com
campanes de vent o un carilló - cada nota fa el seu propi decay via CC11.
X: Ritme (temps entre campanes: lent/rapid)
Y: Escala del carilló (Pentatònica, Mística, Whole-tone, Lidia, Japonesa)
Z: Octava (2-5)
Doble click: canvi de tonalitat
"""
import time
import random
from modes.base_mode import BaseMode
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

# Escales de campanes (intervals semitones des de la tònica)
_SCALES = (
    (0, 2, 4, 7, 9),             # Pentatònica: timbre asiàtic, bronzós
    (0, 1, 4, 6, 8, 10),         # Mística (Scriabin): etèria, mística
    (0, 2, 4, 6, 8, 10),         # Tons sencers: impressionista, Debussy
    (0, 2, 4, 6, 7, 9, 11),      # Lídia: brillant, màgica
    (0, 2, 5, 7, 9),             # Japonesa (Hirajoshi): clara, zen
)
_SNAMES = ('Pentatònica', 'Mística', 'Whole-tone', 'Lídia', 'Japonesa')

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


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


class ModeToCampanes(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "ToCampanes"
        self.key_idx   = 0
        self.octave    = 4
        self.scale_idx = 0

        # Scheduling de la propera campana
        self.next_bell_t   = 0.0
        self.bell_interval = 0.8  # temps entre campanes (s)

        # Notes actives i el seu decay individual
        # Cada campana: (note, birth_time, decay_dur, expression_peak)
        self.active_bells = []

        # Doble click
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.dbl_thr      = 0.4

        self.active_notes = []

    def setup(self):
        self.initialized  = True
        self.next_bell_t  = time.monotonic()
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.active_bells = []
        # Reverb abundant — campanes viuen a l'espai
        _cc(self.midi_out, 91, 80)
        _cc(self.midi_out, 11, 127)
        print(f"ToCampanes: {_SNAMES[self.scale_idx]} {_KEYS[self.key_idx]}")

    def _pick_note(self):
        """Escull nota aleatòria dintre de l'escala i octava actual."""
        scale = _SCALES[self.scale_idx]
        key_off = _OFF[self.key_idx]
        # Afegir possibilitat d'octava +1 per rang més ric
        oct_spread = random.choice([0, 0, 1])  # 2/3 vegades octava actual, 1/3 octava amunt
        interval = random.choice(scale)
        note = (self.octave + oct_spread) * 12 + key_off + interval
        return max(36, min(108, note))

    def _fire_bell(self, now):
        """Dispara una campana amb decay natural."""
        note = self._pick_note()
        # Velocitat aleatòria: simula campanes de diferent intensitat
        vel  = random.randint(55, 105)
        # Durada del decay: les notes greus duren més
        decay_dur = 1.5 + (note / 127.0) * 2.5  # 1.5s a 4s
        _on(self.midi_out, note, vel)
        self.active_bells.append({
            'note':      note,
            'born':      now,
            'decay_dur': decay_dur,
            'last_expr': 127,
        })
        self.active_notes = [b['note'] for b in self.active_bells]

    def _process_decays(self, now):
        """Aplica el decay natural de CC11 a cada campana activa."""
        expired = []
        for bell in self.active_bells:
            age     = now - bell['born']
            t_norm  = min(1.0, age / bell['decay_dur'])
            # Corba de decay exponencial: sona natural
            expr    = int(127 * (1.0 - t_norm) ** 1.8)

            if expr <= 0:
                _off(self.midi_out, bell['note'])
                expired.append(bell)
            else:
                # Actualitzar CC11 (Expression) d'aquesta campana
                # Com que CC11 es global, apliquem el la campana mes recent
                if bell == self.active_bells[-1]:
                    if abs(expr - bell['last_expr']) >= 2:
                        _cc(self.midi_out, 11, expr)
                        bell['last_expr'] = expr

        for b in expired:
            self.active_bells.remove(b)
        self.active_notes = [b['note'] for b in self.active_bells]

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # X: Interval entre campanes (4s lent → 0.15s ràpid)
        # Rang molt llarg: des de silenci espaciat fins a pluja de campanes
        self.bell_interval = max(0.15, 4.0 - (x / 127.0) * 3.85)
        # Variació aleatòria ±25% per naturalitat
        jitter = self.bell_interval * 0.25

        # Y: Escala
        new_scale = min(4, int((y / 127.0) * 5))
        if new_scale != self.scale_idx:
            self.scale_idx = new_scale
            print(f"ToCampanes: {_SNAMES[self.scale_idx]}")

        # Z: Octava (2-5)
        new_oct = 2 + int((z / 127.0) * 3.99)
        if new_oct != self.octave:
            self.octave = new_oct

        # Processar decays de campanes actives
        self._process_decays(now)

        # Disparar nova campana quan toca
        if now >= self.next_bell_t:
            self._fire_bell(now)
            self.next_bell_t = now + self.bell_interval + random.uniform(-jitter, jitter)

        # Doble click: canvi de tonalitat
        for i in range(min(len(button_states), 16)):
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap = now - self.last_release[i]
                if 0.05 < gap < self.dbl_thr:
                    self.last_release[i] = 0.0
                    self.key_idx = (self.key_idx + 1) % 12
                    print(f"ToCampanes: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {
            'key':   _KEYS[self.key_idx],
            'scale': _SNAMES[self.scale_idx],
            'bells': len(self.active_bells),
        }

    def stop(self):
        self.cleanup()

    def cleanup(self):
        for bell in list(self.active_bells):
            try:
                _off(self.midi_out, bell['note'])
            except Exception:
                pass
        self.active_bells = []
        self.active_notes = []
        _cc(self.midi_out, 11, 127)
        _cc(self.midi_out, 91, 0)
        try:
            self.midi_out.send(ControlChange(123, 0))
            self.midi_out.send(ControlChange(120, 0))
        except Exception:
            pass
