"""
Mode Resonàncies - Generador de drones i ressonàncies interactiu
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeResonancies(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Resonàncies"
        self.oscillators = []
        self.last_update = 0
        
    def setup(self):
        self.initialized = True
        self.oscillators = []
        self.last_update = time.monotonic()
        
        # Inicialitzar oscil·ladors
        self._init_oscillators()
        
    def _init_oscillators(self):
        """Inicialitza els oscil·ladors de ressonància"""
        self.oscillators = []
        
        # Crear 3 oscil·ladors amb freqüències relacionades
        base_freq = 110.0  # La2
        ratios = [1.0, 1.5, 2.0, 2.5, 3.0]
        
        for i, ratio in enumerate(ratios):
            self.oscillators.append({
                'freq': base_freq * ratio,
                'phase': 0.0,
                'amp': 0.3 if i == 0 else 0.1,  # El primer oscil·lador és més fort
                'mod_phase': random.random() * 2 * math.pi,
                'mod_freq': 0.1 + random.random() * 0.5,
                'mod_amp': 0.0,
                'note': 0,
                'channel': i % 16
            })
    
    def _freq_to_midi_note(self, freq):
        """Converteix una freqüència a una nota MIDI assegurant-se que estigui dins del rang MIDI"""
        try:
            # Utilitzem math.log amb base 2 en lloc de math.log2 per compatibilitat
            note = int(12 * (math.log(max(8.0, min(freq, 12543.0)) / 440.0) / math.log(2)) + 69)
            # Assegurar que la nota estigui dins del rang MIDI (0-127)
            return max(0, min(127, note))
        except (ValueError, ZeroDivisionError):
            return 60  # Retorna Do central en cas d'error
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = min(0.1, current_time - self.last_update)
        self.last_update = current_time
        
        x, y, z = pot_values
        
        # Actualitzar paràmetres dels oscil·ladors amb suavitzat
        target_freq = 55.0 + (x / 127.0) * 880.0  # A1 a A5
        target_harmonicity = 1.0 + (y / 127.0) * 4.0  # 1x a 5x harmònics
        target_modulation = z / 127.0  # 0 a 1 modulació
        
        # Aplicar suavitzat als canvis per millorar la fluïdesa
        if not hasattr(self, 'current_freq'):
            self.current_freq = target_freq
            self.current_harmonicity = target_harmonicity
            self.current_modulation = target_modulation
        else:
            # Suavitzat exponencial per canvis més fluïts
            smoothing = 0.2
            self.current_freq += (target_freq - self.current_freq) * smoothing
            self.current_harmonicity += (target_harmonicity - self.current_harmonicity) * smoothing
            self.current_modulation += (target_modulation - self.current_modulation) * smoothing
        
        base_freq = self.current_freq
        harmonicity = self.current_harmonicity
        modulation = self.current_modulation
        
        # Aturar només les notes que estan sonant i han canviat
        for osc in self.oscillators:
            # Només processar si hi ha una nota activa
            if 'note' in osc and osc['note'] is not None and 'channel' in osc:
                try:
                    # Crear i enviar NoteOff per a la nota actual
                    note_off_msg = self.note_off(osc['note'], 0)
                    note_off_msg.channel = osc['channel']
                    self.midi_out.send(note_off_msg)
                except (ValueError, KeyError, AttributeError) as e:
                    # Registrar l'error i continuar
                    print(f"Error aturant nota {osc.get('note')}: {str(e)}")
        
        # Actualitzar i tocar els oscil·ladors
        for i, osc in enumerate(self.oscillators):
            # Actualitzar freqüència basada en la posició del potenciòmetre
            ratio = 1.0 + i * 0.5
            osc['freq'] = base_freq * (ratio ** harmonicity)
            
            # Actualitzar modulació amb suavitzat
            osc['mod_phase'] = (osc['mod_phase'] + dt * osc['mod_freq']) % (2 * math.pi)
            mod = math.sin(osc['mod_phase']) * modulation
            
            # Aplicar modulació a l'amplitud i freqüència amb límits
            current_freq = max(8.0, min(12543.0, osc['freq'] * (1.0 + mod * 0.2)))
            current_amp = max(0.0, min(1.0, osc['amp'] * (0.8 + 0.4 * (mod + 1) / 2)))
            
            # Convertir a nota MIDI amb control de rango
            note = self._freq_to_midi_note(current_freq)
            velocity = max(1, min(127, int(current_amp * 127)))  # Velocitat mínima 1, màxima 127
            
            # Reproduir la nota si ha canviat significativament
            current_note = osc.get('note')
            last_velocity = osc.get('last_velocity', 0)
            
            if (current_note is None or 
                abs(note - current_note) > 2 or 
                abs(velocity - last_velocity) > 10):
                
                try:
                    current_channel = osc.get('channel', 0)  # Canal per defecte 0 si no està definit
                    
                    # Aturar la nota actual si n'hi ha una
                    if current_note is not None:
                        try:
                            note_off_msg = self.note_off(current_note, 0)
                            note_off_msg.channel = current_channel
                            self.midi_out.send(note_off_msg)
                        except (ValueError, AttributeError) as e:
                            print(f"Error aturant nota {current_note}: {str(e)}")
                    
                    # Tocar la nova nota
                    try:
                        note_on_msg = self.note_on(note, velocity)
                        note_on_msg.channel = current_channel
                        self.midi_out.send(note_on_msg)
                        
                        # Actualitzar l'estat de l'oscil·lador
                        osc['note'] = note
                        osc['last_velocity'] = velocity
                        
                    except (ValueError, AttributeError) as e:
                        print(f"Error tocant nota {note}: {str(e)}")
                        
                except Exception as e:
                    print(f"Error en l'actualització de l'oscil·lador: {str(e)}")
        
        return {
            'mode': 'Resonàncies',
            'freq_base': f"{base_freq:.1f} Hz",
            'harmònics': f"{harmonicity:.1f}x",
            'modulació': f"{modulation*100:.0f}%"
        }
    
    def cleanup(self):
        """Atura totes les notes i neteja els recursos"""
        notes_to_stop = []
        
        # Aturar totes les notes dels oscil·ladors
        for osc in self.oscillators:
            if 'note' in osc and osc['note'] is not None:
                try:
                    # Obtenir la nota i el canal
                    note = osc['note']
                    channel = osc.get('channel', 0)  # Canal per defecte 0 si no està definit
                    velocity = 0  # Velocitat 0 per NoteOff
                    
                    # Crear el missatge NoteOff
                    note_off_msg = self.note_off(note, velocity)
                    
                    # Establir el canal si està definit
                    if channel is not None:
                        note_off_msg.channel = channel
                    
                    # Enviar el missatge i afegir la nota a la llista en format (nota, velocitat, canal)
                    self.midi_out.send(note_off_msg)
                    notes_to_stop.append([note, velocity, channel])  # Format correcte que espera el ModeManager
                    
                    # Marcar la nota com a aturada
                    osc['note'] = None
                    
                except (ValueError, KeyError, AttributeError) as e:
                    # Ignorar errors i continuar amb la següent nota
                    print(f"Error aturant nota {osc.get('note')}: {str(e)}")
                    continue
        
        return notes_to_stop
