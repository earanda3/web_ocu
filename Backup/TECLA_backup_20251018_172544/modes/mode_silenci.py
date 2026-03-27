"""
Mode Silenci - Atura tot el so i manté el sintetitzador en silenci
Versió optimitzada per a mínima latència
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff

class ModeSilenci(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config or {})
        self.name = "SILENCI"
        self.last_cleanup = 0
        self.cleanup_interval = 2.0  # Segons entre neteges completes
        
    def setup(self):
        """Inicialitza el mode silenci"""
        self.initialized = True
        # Neteja ràpida inicial
        self._fast_cleanup()
        
    def update(self, pot_values, button_states):
        """Actualitza l'estat del mode"""
        current_time = time.monotonic()
        
        # Fer neteja completa cada cert temps
        if current_time - self.last_cleanup > self.cleanup_interval:
            self.cleanup()
        
        return {'mode': 'SILENCI', 'status': 'TOT ATURAT'}
        
    def _fast_cleanup(self):
        """Neteja ràpida - només envia All Sound Off"""
        try:
            # Enviar All Sound Off (Control Change 120) al canal 0 (omès per compatibilitat)
            # Això és més ràpid que enviar-ho a tots els canals
            self.midi_out.send(ControlChange(120, 0))
        except Exception:
            pass
    
    def cleanup(self):
        """Neteja completa - optimitzada per ser ràpida"""
        try:
            # 1. Enviar All Sound Off (Control Change 120) a tots els canals
            #    En un sol missatge quan sigui possible (sense especificar canal)
            self.midi_out.send(ControlChange(120, 0))
            
            # 2. Enviar All Notes Off (Control Change 123) a tots els canals
            self.midi_out.send(ControlChange(123, 0))
            
            # 3. Enviar note_off per a les notes més probables
            #    Sense especificar canal per a major velocitat
            for note in range(24, 96):  # Rango de notas más comunes
                self.midi_out.send(NoteOff(note, 0))
            
            self.last_cleanup = time.monotonic()
            
        except Exception:
            # En cas d'error, fer una neteja ràpida
            self._fast_cleanup()
            
        return []
