"""Makina - DJ Sisu, Pastis i Buenri. Kick rapid, piano euforic, bas que corre."""
import time
from modes.base_mode import BaseMode

# Riffs de piano makina iconics (intervals sobre la tònica, en semítons)
# Cadascun es un patró de 8 notes que fa loop rapid
RIFFS = [
    [0,4,7,4, 0,4,7,12],   # Ascendent classic: C-E-G-E-C-E-G-C8
    [0,2,4,7, 9,7,4,2],    # Running: C-D-E-G-A-G-E-D
    [0,0,7,0, 4,0,7,0],    # Stomper: C-C-G-C-E-C-G-C
    [4,7,9,7, 4,2,0,2],    # Happy: E-G-A-G-E-D-C-D
]

# Notas del baix: Tonica a beat 0/8, Quinta a beat 4/12
BASS_STEPS = {0: 0, 4: 7, 8: 0, 12: 7}

class ModeMakina(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Makina"
        self.step = -1
        self.riff_step = 0
        self.t = time.monotonic()
        self.kick_note = None
        self.bass_note = None
        self.lead_note = None
        self.kick_off_t = 0.0
        self.bass_off_t = 0.0
        self.lead_off_t = 0.0

    def setup(self):
        self.initialized = True
        self.step = -1
        self.riff_step = 0
        self.t = time.monotonic()
        self.kick_note = self.bass_note = self.lead_note = None

    def update(self, pot_values, button_states):
        now = time.monotonic()
        x, y, z = pot_values

        # X = BPM (180-240 — territori Makina pura)
        bpm = 180 + int((x / 127.0) * 60)
        step_dur = 60.0 / (bpm * 4)

        # Apagar notes si han expirat
        if self.kick_note and now >= self.kick_off_t:
            self.midi_out.send(self.note_off(self.kick_note, 0))
            self.kick_note = None
        if self.bass_note and now >= self.bass_off_t:
            self.midi_out.send(self.note_off(self.bass_note, 0))
            self.bass_note = None
        if self.lead_note and now >= self.lead_off_t:
            self.midi_out.send(self.note_off(self.lead_note, 0))
            self.lead_note = None

        if now - self.t < step_dur:
            return {}
        self.t = now
        self.step = (self.step + 1) % 16

        # Y = riff (0-3) + tonalitat base
        riff_idx = int((y / 127.0) * (len(RIFFS) - 0.01))
        riff = RIFFS[riff_idx]
        # Tònica: C4 (60) a C5 (72) — el piano Makina sona agut i brillant
        tonic = 60 + int((z / 127.0) * 12)

        # --- KICK: 4-on-the-floor a velocitat extrema ---
        if self.step % 4 == 0:
            kick_vel = 125 if self.step == 0 else 115
            self.midi_out.send(self.note_on(36, kick_vel))
            self.kick_note = 36
            self.kick_off_t = now + 0.025  # 25ms, molt percussiu i sec

        # --- PIANO/LEAD: Riff ràpid, avança cada step ---
        riff_note = tonic + riff[self.riff_step % len(riff)]
        riff_note = max(0, min(127, riff_note))
        self.riff_step += 1

        # El piano sona molt ràpid: durada de 70% del step
        if self.lead_note:
            self.midi_out.send(self.note_off(self.lead_note, 0))
        # Velocity: nota 0 (tònica) i nota 4 (quarta/quinta) més fortes
        lead_vel = 100 if (self.riff_step % len(riff)) in (0, 4) else 82
        self.midi_out.send(self.note_on(riff_note, lead_vel))
        self.lead_note = riff_note
        self.lead_off_t = now + step_dur * 0.7

        # --- BAS: corre amb la tònica i la quinta ---
        if self.step in BASS_STEPS:
            offset = BASS_STEPS[self.step]
            b = tonic - 24 + offset  # una octava i mitja avall del piano
            b = max(0, min(127, b))
            if self.bass_note:
                self.midi_out.send(self.note_off(self.bass_note, 0))
            self.midi_out.send(self.note_on(b, 95))
            self.bass_note = b
            self.bass_off_t = now + step_dur * 3.5

        return {'bpm': bpm, 'step': self.step, 'riff': riff_idx}

    def cleanup(self):
        for n in [self.kick_note, self.bass_note, self.lead_note]:
            if n is not None:
                self.midi_out.send(self.note_off(n, 0))
        self.kick_note = self.bass_note = self.lead_note = None
        return []
