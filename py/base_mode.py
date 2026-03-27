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
        
        # Actualitzar directament el PWM cada vegada que es toca una nota
        self.update_pwm_frequency(note & 0x7F)
        
        return NoteOn(note & 0x7F, velocity & 0x7F)
    
    def note_off(self, note, velocity=0):
        """
        Crea un missatge MIDI Note Off i silencia el PWM.
        
        Args:
            note: Número de nota MIDI (0-127)
            velocity: Velocitat de la nota (0-127)
            
        Returns:
            Objecte NoteOff de adafruit_midi
        """
        from adafruit_midi.note_off import NoteOff
        
        # Silenciar el PWM mantenint la mateixa freqüència
        try:
            import main
            if hasattr(main, 'pwm'):
                # Mantenir freqüència pero silenciar
                main.pwm.duty_cycle = 0
        except Exception:
            pass  # No interrumpir per errors en el PWM
        
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
    
    def update_pwm_frequency(self, note):
        """
        Actualitza directament la freqüència del PWM per a una nota MIDI donada.
        Garanteix que el PWM s'actualitza SEMPRE, independentment d'altres operacions.
        
        Args:
            note: Número de nota MIDI (0-127)
        """
        try:
            # Importar directament els objectes necessaris
            import main
            import pwmio
            import board
            
            # Calcular la freqüència
            freq = main.midi_to_frequency(note)
            
            # Comprovar si el PWM ja existeix globalment
            if hasattr(main, 'pwm') and isinstance(main.pwm, pwmio.PWMOut):
                main.pwm.frequency = freq
                main.pwm.duty_cycle = 32767  # 50% duty cycle
                return True
                
            # Si no existeix a main, buscar a l'objecte actual
            if hasattr(self, '_pwm_instance') and self._pwm_instance is not None:
                self._pwm_instance.frequency = freq
                self._pwm_instance.duty_cycle = 32767
                return True
                
            # Configuració inicial - intentar accedir al pin amb seguretat
            try:
                # Inicialitzar PWM al primer ús
                self._pwm_instance = pwmio.PWMOut(board.GP22, frequency=freq, duty_cycle=32767, variable_frequency=True)
                # També guardar a main per accés global
                main.pwm = self._pwm_instance
                return True
                
            except ValueError as e:
                # Si el pin ja està en ús, buscar alternatives
                if "in use" in str(e):
                    # Intentar accedir directament si existeix en algún lloc
                    try:
                        # Buscar en globals
                        import sys
                        for module_name in list(sys.modules.keys()):
                            try:
                                module = sys.modules[module_name]
                                if hasattr(module, 'pwm'):
                                    # Si trobem un PWM existent, utilitzar-lo
                                    self._pwm_instance = module.pwm
                                    self._pwm_instance.frequency = freq
                                    self._pwm_instance.duty_cycle = 32767
                                    return True
                            except:
                                pass
                    except:
                        pass
                else:
                    print(f"No es pot inicialitzar PWM: {e}")
                    
        except ImportError as e:
            print(f"Mòdul no trobat: {e}")
        except Exception as e:
            print(f"Error actualitzant PWM: {e}")
            
        return False
    
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
