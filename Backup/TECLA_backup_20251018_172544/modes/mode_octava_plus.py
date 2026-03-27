"""
Mode Octava+ - Mode especial per augmentar l'octava de tots els modes
"""
import time
from modes.base_mode import BaseMode

class ModeOctavaPlus(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Octava+"
        self.last_update = time.monotonic()
        
    def setup(self):
        """Inicialitza el mode i incrementa l'octava global"""
        self.initialized = True
        
        # Anem a trobar el ModeManager
        from modes.mode_manager import ModeManager
        mode_manager = None
        
        # Cerquem el ModeManager en el context global
        import sys
        for var_name in dir(sys.modules['__main__']):
            var = getattr(sys.modules['__main__'], var_name)
            if isinstance(var, ModeManager):
                mode_manager = var
                break
        
        # Si hem trobat el ModeManager, canviem l'octava
        if mode_manager:
            if hasattr(mode_manager, '_shift_octave'):
                mode_manager._shift_octave(1)  # Augmentar una octava
                print("Octava augmentada")
            
            # Retornar al mode anterior
            if hasattr(mode_manager, 'return_to_previous_mode'):
                mode_manager.return_to_previous_mode()
        else:
            print("No s'ha pogut trobar el ModeManager")
        
    def update(self, pot_values, button_states):
        # No fem res aquí, perquè el mode retorna immediatament al mode anterior
        return {
            'mode': 'Octava+',
            'status': 'Augmentant octava...'
        }
        
    def cleanup(self):
        # No cal fer res aquí ja que no generem notes
        return []
