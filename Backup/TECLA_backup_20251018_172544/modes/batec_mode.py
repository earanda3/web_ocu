"""
Mode Batec: Simula el so d'un batec cardíac amb dues notes
"""
import time
from .base_mode import BaseMode
from ..utils.helpers import steps, steps_control

class BatecMode(BaseMode):
    """
    Mode Batec: Simula el so d'un batec cardíac amb dues notes (LUB-DUB).
    """
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Mode Batec"
        self.last_beat_time = 0
        self.beat_phase = 0  # 0 = silenci, 1 = LUB, 2 = DUB
        self.bpm = 60
        self.low_note = 36  # C2
        self.high_note = 48  # C3
        
    def setup(self):
        """Inicialitza l'estat del mode"""
        super().setup()
        self.last_beat_time = time.monotonic()
        self.beat_phase = 0
        
    def update(self, pot_values, button_states):
        """Actualitza l'estat del mode"""
        super().update(pot_values, button_states)
        
        # Llegir valors dels potenciòmetres
        x, y, z = pot_values
        
        # Actualitzar paràmetres basats en els potenciòmetres
        self.bpm = 30 + steps_control(x)  # 30-157 BPM
        self.low_note = 36 + (steps_control(y) // 10)  # 36-48 (C2-C3)
        self.high_note = self.low_note + 12  # Una octava per sobre
        
        # Controlar el ritme del batec
        current_time = time.monotonic()
        beat_interval = 60.0 / self.bpm
        
        # Determinar si cal avançar a la següent fase del batec
        if current_time - self.last_beat_time >= beat_interval:
            self.beat_phase = (self.beat_phase + 1) % 3
            self.last_beat_time = current_time
            
        return {
            'bpm': self.bpm,
            'low_note': self.low_note,
            'high_note': self.high_note,
            'phase': self.beat_phase
        }
        
    def get_notes_to_play(self):
        """Retorna les notes que s'han de reproduir en aquest cicle"""
        notes = []
        
        # Reproduir LUB o DUB segons la fase actual
        if self.beat_phase == 1:  # LUB
            notes.append((self.low_note, 100, 0))  # Nota greu
        elif self.beat_phase == 2:  # DUB
            notes.append((self.high_note, 80, 0))   # Nota aguda
            
        return notes
        
    def get_notes_to_stop(self):
        """Retorna les notes que s'han d'aturar en aquest cicle"""
        notes = []
        
        # Aturar la nota anterior quan canvia la fase
        if self.beat_phase == 0:  # Acaba de sonar DUB
            notes.append((self.high_note, 0))
        elif self.beat_phase == 1:  # Acaba de sonar LUB
            notes.append((self.low_note, 0))
            
        return notes
        
    def get_mode_info(self):
        """Retorna informació sobre el mode actual"""
        return {
            'name': 'Mode Batec',
            'description': 'Simula el batec cardíac amb notes LUB-DUB',
            'version': '1.0',
            'parameters': {
                'bpm': self.bpm,
                'low_note': self.low_note,
                'high_note': self.high_note
            }
        }
