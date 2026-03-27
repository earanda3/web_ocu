"""
Mode Rítmic - Genera patrons rítmics amb control de kick, velocitat i pitch
"""
import time
import math
from modes.base_mode import BaseMode

class ModeRitmicLoop(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Rítmic"
        self.bpm = 120
        self.last_beat = 0
        self.beat_interval = 0.5  # Segons per beat
        self.kick_pattern = [1, 0, 0, 0, 1, 0, 1, 0]  # Patró de kick inicial
        self.current_step = 0
        self.notes_playing = set()
        
    def setup(self):
        self.initialized = True
        self.last_beat = time.monotonic()
        self.notes_playing = set()
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Control de BPM (30-240 BPM)
        self.bpm = 30 + (y / 127.0) * 210
        self.beat_interval = 60.0 / (self.bpm * 2)  # 1/8 notes
        
        # Control de distorsió (afecta la velocitat)
        distortion = x / 127.0
        velocity = int(70 + (distortion * 50))
        
        # Control de pitch (afecta la nota)
        pitch_offset = int((z / 127.0) * 24)  # Fins a 2 octaves
        kick_note = 36 + pitch_offset  # Nota base del kick (C1)
        
        # Avançar el patró
        if current_time - self.last_beat >= self.beat_interval:
            self.last_beat = current_time
            
            # Aturar notes anteriors
            for note in list(self.notes_playing):
                self.midi_out.send(self.note_off(note, 0))
            self.notes_playing.clear()
            
            # Reproduir el kick si és el moment al patró
            if self.kick_pattern[self.current_step]:
                self.midi_out.send(self.note_on(kick_note, velocity))
                self.notes_playing.add(kick_note)
            
            # Següent pas del patró
            self.current_step = (self.current_step + 1) % len(self.kick_pattern)
        
        return {
            'bpm': self.bpm,
            'step': self.current_step,
            'velocity': velocity,
            'pitch': kick_note
        }
    
    def cleanup(self):
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        return [(note, 0) for note in notes_to_stop]
