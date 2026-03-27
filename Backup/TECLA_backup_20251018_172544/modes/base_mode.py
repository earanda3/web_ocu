"""
Classe base per a tots els modes d'operació
"""

class BaseMode:
    """
    Classe base que defineix la interfície comuna per a tots els modes d'operació.
    Tots els modes han d'heretar d'aquesta classe i implementar els seus mètodes.
    """
    def __init__(self, midi_out, config=None):
        """
        Inicialitza el mode.
        
        Args:
            midi_out: Instància de sortida MIDI
            config: Diccionari amb configuració addicional (opcional)
        """
        self.midi_out = midi_out
        self.config = config or {}
        self.initialized = False
        self.iteration = 0
        
    def setup(self):
        """
        Inicialitza l'estat del mode. S'executa una vegada abans de començar.
        """
        self.initialized = True
        self.iteration = 0
        
    def cleanup(self):
        """
        Neteja els recursos del mode. S'executa quan es canvia a un altre mode.
        """
        pass
        
    def update(self, pot_values, button_states):
        """
        Actualitza l'estat del mode en funció dels valors dels potenciòmetres i estats dels botons.
        
        Args:
            pot_values: Llista amb els valors dels potenciòmetres [x, y, z]
            button_states: Llista amb els estats dels botons [b0, b1, ..., b15]
            
        Returns:
            Diccionari amb informació de depuració (opcional)
        """
        self.iteration += 1
        return {}
    
    def get_notes_to_play(self):
        """
        Retorna una llista de tuples (nota, velocitat) que s'han de reproduir.
        Si no hi ha notes per reproduir, retorna una llista buida.
        """
        return []
        
    def note_on(self, note, velocity=127):
        """
        Crea un missatge MIDI Note On.
        
        Args:
            note: Número de nota MIDI (0-127)
            velocity: Velocitat de la nota (0-127)
            
        Returns:
            Objecte NoteOn de adafruit_midi
        """
        from adafruit_midi.note_on import NoteOn
        return NoteOn(note & 0x7F, velocity & 0x7F)
    
    def note_off(self, note, velocity=0):
        """
        Crea un missatge MIDI Note Off.
        
        Args:
            note: Número de nota MIDI (0-127)
            velocity: Velocitat de la nota (0-127)
            
        Returns:
            Objecte NoteOff de adafruit_midi
        """
        from adafruit_midi.note_off import NoteOff
        return NoteOff(note & 0x7F, velocity & 0x7F)
    
    def get_notes_to_stop(self):
        """
        Retorna una llista de tuples (note, channel) que s'han d'aturar.
        
        Returns:
            Llista de tuples (note, channel)
        """
        return []
    
    def get_control_changes(self):
        """
        Retorna una llista de canvis de control MIDI a enviar.
        
        Returns:
            Llista de tuples (control, value, channel)
        """
        return []
    
    def get_mode_info(self):
        """
        Retorna informació sobre el mode actual.
        
        Returns:
            Diccionari amb informació del mode (nom, descripció, etc.)
        """
        return {
            'name': 'Base Mode',
            'description': 'Mode base abstracte',
            'version': '1.0'
        }
