"""
Mode Part - Estil tintinnabuli d'Arvo Part: silenci, campanes i drones
La tecnica tintinnabuli: una veu de campana (tríada) + una veu de melodia
X: Velocitat de les campanes (molt lent a lleuger)
Y: Figura de campana (Fratres, Spiegel, Alina, Tabula Rasa, Fur Alina)
Z: Profunditat del drone de baix (0=sense drone, 127=drone dens)
Doble click: canvi de tonalitat
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# Tintinnabuli: la veu de campana sempre es mou per la tríada
# La veu T (tintinnabuli) usa intervals: tònica, terça, quinta de la tríada major
_TINTINNABULI = (0, 4, 7, 12, 7, 4, 0, -5)  # T-veu clàssica

# La veu M (melodia) es mou per graus esglaonats
_PATTERNS = (
    # Fratres: pas a pas, molt lent, transcendent
    (0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0, -1),
    # Spiegel im Spiegel: reflexos, amunt i avall simetricament
    (0, 2, 4, 7, 9, 12, 9, 7, 4, 2, 0, 2),
    # Alina: molt simple, quasi res
    (0, 2, 0, 4, 0, 7, 0, 4, 0, 2, 0, 0),
    # Tabula Rasa: taula rasa, nota sola repetida
    (0, 0, 4, 0, 0, 7, 0, 0, 12, 0, 0, 7),
    # Fur Alina: tendra, una nota i silenci
    (0, 4, 7, 4, 0, 0, 7, 12, 7, 0, 4, 0),
)
_PNAMES = ('Fratres', 'Spiegel', 'Alina', 'TabulaRasa', 'FurAlina')

_KEYS = ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B')
_OFF  = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


class ModePart(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Part"
        self.key_idx    = 0
        self.octave     = 4
        self.pat_idx    = 0
        self.step       = 0
        self.t_step     = 0      # veu tintinnabuli independent
        self.mel_note   = -1     # nota de melodia activa
        self.tin_note   = -1     # nota de campana activa
        self.drone_notes = []    # notes del drone baix
        self.next_note_t = 0.0
        self.speed      = 0.6    # Part és lent per defecte
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.dbl_thr      = 0.4

    def setup(self):
        self.initialized  = True
        self.last_release = [0.0] * 16
        self.last_btn     = [False] * 16
        self.next_note_t  = time.monotonic()
        self.step = 0
        self.t_step = 0
        # Part: molta reverberació (l'espai és part del so)
        self._cc(91, 90)
        self._cc(64, 0)
        print(f"Part: {_PNAMES[self.pat_idx]} {_KEYS[self.key_idx]}")

    def _root(self, octave=None):
        if octave is None:
            octave = self.octave
        return octave * 12 + _OFF[self.key_idx]

    def _cc(self, cc, val):
        try:
            self.midi_out.send(ControlChange(cc, max(0, min(127, val))))
        except Exception:
            pass

    def _update_drone(self, depth):
        """Drone de baix: tònica + quinta, octava inferior."""
        target_depth = int(depth * 60)  # velocitat màxima del drone
        root = self._root(octave=self.octave - 1)
        desired = [root, root + 7] if depth > 0.05 else []

        # Si les notes han canviat, reajustar
        if set(self.drone_notes) != set(desired):
            for n in self.drone_notes:
                try:
                    self.midi_out.send(self.note_off(n, 0))
                except Exception:
                    pass
            self.drone_notes = []
            for n in desired:
                note = max(12, min(84, n))
                try:
                    self.midi_out.send(self.note_on(note, target_depth if target_depth > 0 else 1))
                    self.drone_notes.append(note)
                except Exception:
                    pass

    def _play_step(self):
        pat = _PATTERNS[self.pat_idx]
        root = self._root()

        # Veu M (melodia): graus de l'escala
        mel_interval = pat[self.step % len(pat)]
        mel = max(24, min(108, root + mel_interval))

        # Veu T (tintinnabuli): sempre dins la tríada
        tin_interval = _TINTINNABULI[self.t_step % len(_TINTINNABULI)]
        tin = max(24, min(108, root + tin_interval + 12))  # una octava amunt

        # Aturar notes anteriors
        if self.mel_note >= 0:
            self.midi_out.send(self.note_off(self.mel_note, 0))
        if self.tin_note >= 0:
            self.midi_out.send(self.note_off(self.tin_note, 0))

        # Tocar noves notes (mel_interval=0 → silenci implícit a Fur Alina, etc.)
        if mel_interval != 0 or self.step % 4 == 0:  # sempre toca el primer de cada grup
            self.midi_out.send(self.note_on(mel, 65))
            self.mel_note = mel
        else:
            # "Silenci" (nota molt suau)
            self.midi_out.send(self.note_on(mel, 25))
            self.mel_note = mel

        self.midi_out.send(self.note_on(tin, 50))
        self.tin_note = tin

        self.step   = (self.step + 1) % len(pat)
        self.t_step = (self.t_step + 1) % len(_TINTINNABULI)

    def update(self, pot_values, button_states):
        x, y, z = pot_values
        now = time.monotonic()

        # X: Velocitat (3s molt lent → 0.3s moderat)
        self.speed = max(0.3, 3.0 - (x / 127.0) * 2.7)

        # Y: Figura
        new_pat = min(4, int((y / 127.0) * 5))
        if new_pat != self.pat_idx:
            self.pat_idx = new_pat
            self.step = 0
            self.t_step = 0

        # Z: Drone de baix (0=silenci, 127=dens)
        self._update_drone(z / 127.0)

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
                    self.t_step = 0
                    # Actualitzar drone a nova tonalitat
                    self._update_drone(z / 127.0 if z > 6 else 0)
                    print(f"Part: {_KEYS[self.key_idx]}")
                else:
                    self.last_release[i] = now
            self.last_btn[i] = cur

        return {
            'key':  _KEYS[self.key_idx],
            'fig':  _PNAMES[self.pat_idx],
            'drone': 'ON' if self.drone_notes else 'OFF',
        }

    def cleanup(self):
        for n in (self.mel_note, self.tin_note):
            if n >= 0:
                try:
                    self.midi_out.send(self.note_off(n, 0))
                except Exception:
                    pass
        self.mel_note = self.tin_note = -1
        for n in self.drone_notes:
            try:
                self.midi_out.send(self.note_off(n, 0))
            except Exception:
                pass
        self.drone_notes = []
        self._cc(91, 0)
        self._cc(123, 0)
        self._cc(120, 0)
