"""MarkovGenre - Cadena Markov de genere musical. X:tempo Y:genere Z:expressivitat"""
import time, random
from modes.base_mode import BaseMode

# Cada genere: escala, pesos de moviment [-2,-1,0,+1,+2], vel min/max, swing
GENRES = [
    # Jazz: cromàtic, salts, sorpreses, velocitat variada
    {'name':'Jazz',  's':[0,2,4,5,7,9,10,11], 'w':[0.4,0.7,0.1,0.7,0.4], 'vl':55,'vh':115,'sw':0.6},
    # Blues: escala de blues, nota repetida, respira, expressiu
    {'name':'Blues', 's':[0,3,5,6,7,10],       'w':[0.2,0.6,0.5,0.6,0.15],'vl':45,'vh':105,'sw':0.4},
    # Soul: pentatonica menor, molt vocal, suau i continu
    {'name':'Soul',  's':[0,3,5,7,10],         'w':[0.1,0.9,0.3,0.9,0.1], 'vl':35,'vh':90, 'sw':0.2},
    # Groove: doria, repeticío ritmica, accentuat, sincopat
    {'name':'Groove','s':[0,2,3,5,7,9,10],     'w':[0.2,0.4,0.6,0.4,0.15],'vl':70,'vh':127,'sw':0.5},
]

class ModeMarkovGenre(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "MarkovGenre"
        self.mk_idx = 2
        self.mk_oct = 4
        self.t = time.monotonic()
        self.swing_t = 0.0   # acumulador swing
        self.on_beat = True
        self.cur = None
        self.last_genre = -1

    def setup(self):
        self.initialized = True
        self.mk_idx = 2
        self.mk_oct = 4
        self.t = time.monotonic()
        self.swing_t = 0.0
        self.on_beat = True
        self.cur = None

    def _weighted_choice(self, weights):
        total = sum(weights)
        r = random.random() * total
        acc = 0.0
        for i, w in enumerate(weights):
            acc += w
            if r <= acc:
                return i - 2  # moviment: -2,-1,0,+1,+2
        return 0

    def update(self, pot_values, button_states):
        now = time.monotonic()
        x, y, z = pot_values

        g = GENRES[int((y / 127.0) * (len(GENRES) - 0.01))]

        # Actualitzar nom si canvia gènere
        if y != self.last_genre:
            self.name = g['name']
            self.last_genre = y

        # X = tempo (0.06s a 0.7s per nota)
        base_rate = 0.06 + (1.0 - x / 127.0) * 0.64

        # Swing: notes imparells lleugerament retardades (swing del genere)
        swing = g['sw'] * (z / 127.0) * base_rate * 0.4
        rate = base_rate + (swing if not self.on_beat else 0)

        if now - self.t < rate:
            return {}
        self.t = now
        self.on_beat = not self.on_beat

        scale = g['s']

        # Z = expressivitat: compressa els pesos cap a moviments extrems
        expr = z / 127.0
        w = [wi * (1.0 + expr * abs(i - 2)) for i, wi in enumerate(g['w'])]

        mv = self._weighted_choice(w)
        self.mk_idx = max(0, min(len(scale) - 1, self.mk_idx + mv))

        if self.mk_idx == 0 and mv < 0:
            self.mk_oct = max(3, self.mk_oct - 1)
        elif self.mk_idx == len(scale) - 1 and mv > 0:
            self.mk_oct = min(6, self.mk_oct + 1)

        note = 12 * self.mk_oct + scale[self.mk_idx]
        note = max(0, min(127, note))

        # Velocitat: random dins rang del genere, accentuat al beat 1
        vel = random.randint(g['vl'], g['vh'])
        if self.on_beat:  # accent
            vel = min(127, int(vel * 1.15))

        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
        self.midi_out.send(self.note_on(note, vel))
        self.cur = note

        return {'genre': g['name'], 'note': note, 'swing': round(swing, 3)}

    def cleanup(self):
        if self.cur is not None:
            self.midi_out.send(self.note_off(self.cur, 0))
            self.cur = None
        return []
