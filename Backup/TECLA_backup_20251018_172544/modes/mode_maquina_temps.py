"""
Mode Màquina del Temps - Sampler primitiu amb efectes de degradació analògica
"""
import time
import array
import math
import random
from modes.base_mode import BaseMode

class ModeMaquinaTemps(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Màquina del Temps"
        # Inicialitzar variables
        self.buffer_size = 512  # Mida reduïda del buffer
        self.buffer = array.array('H', [0] * self.buffer_size)  # Buffer circular
        self.buffer_pos = 0
        self.recording = False
        self.playing = False
        self.record_start_time = 0
        self.playback_speed = 1.0
        self.degradation = 0.0
        self.feedback = 0.0
        self.last_play_pos = 0
        self.last_note_time = 0
        self.note_interval = 0.1  # Interval entre notes en segons
        
    def setup(self):
        self.initialized = True
        self.recording = False
        self.playing = False
        self.buffer_pos = 0
        self.buffer = array.array('H', [0] * self.buffer_size)  # Inicialitzar buffer
        self.last_note_time = 0
        
    def _degrade_sample(self, sample, amount):
        """Aplica degradació analògica a una mostra"""
        if random.random() < amount * 0.1:  # Dropouts
            return 0
            
        # Reducció de bits
        bits = max(4, 12 - int(amount * 8))
        max_val = (1 << bits) - 1
        sample = int((sample / 65535.0) * max_val) * (65535 // max_val)
        
        # Soroll analògic
        noise = int((random.random() * 2 - 1) * 1000 * amount)
        return max(0, min(65535, sample + noise))
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Actualitzar paràmetres
        self.playback_speed = 0.25 + (x / 127.0) * 3.75  # 0.25x a 4x
        self.degradation = y / 127.0
        self.feedback = z / 127.0 * 0.9  # Màxim 90% de feedback
        
        # Control de gravació/reproducció amb botons
        if len(button_states) > 0 and button_states[0]:  # Botó 1: Gravar/Aturar
            if not self.recording:
                self.recording = True
                self.playing = False
                self.record_start_time = current_time
                self.buffer_pos = 0
                self.buffer = array.array('H', [0] * self.buffer_size)  # Netejar buffer
                # Iniciar amb un to sinusoïdal
                t = 0
                for i in range(self.buffer_size):
                    self.buffer[i] = int((math.sin(t) * 0.5 + 0.5) * 65535)
                    t += 0.1
                self.buffer_pos = self.buffer_size
                
        if len(button_states) > 1 and button_states[1]:  # Botó 2: Reproduir/Aturar
            if not self.playing and self.buffer_pos > 0:
                self.playing = True
                self.recording = False
                self.last_play_pos = 0
                self.last_note_time = current_time
            elif self.playing:
                self.playing = False
                # Aturar totes les notes en aturar la reproducció
                if hasattr(self, 'last_note'):
                    self.midi_out.send(self.note_off(self.last_note, 0))
                
        # Processar gravació
        if self.recording:
            # Simular entrada d'àudio (en un cas real, això vindria d'un ADC)
            t = current_time - self.record_start_time
            sample = int((math.sin(t * 440 * 2 * math.pi) * 0.5 + 0.5) * 65535)
            
            # Aplicar feedback
            if self.buffer_pos > 0:
                old_sample = self.buffer[(self.buffer_pos - 1) % len(self.buffer)]
                sample = int(sample * (1 - self.feedback) + old_sample * self.feedback)
            
            # Guardar mostra
            self.buffer[self.buffer_pos % len(self.buffer)] = sample
            self.buffer_pos += 1
            
            # Limitar la longitud màxima de gravació
            if self.buffer_pos >= len(self.buffer):
                self.recording = False
                self.playing = True
                self.last_play_pos = 0
                
        # Processar reproducció
        if self.playing and self.buffer_pos > 0 and current_time - self.last_note_time > self.note_interval:
            self.last_note_time = current_time
            
            # Obtenir mostra actual
            play_pos = int(self.last_play_pos) % self.buffer_size
            sample = self.buffer[play_pos]
            
            # Aplicar degradació
            sample = self._degrade_sample(sample, self.degradation)
            
            # Generar nota MIDI basada en el valor de la mostra
            note = 40 + int((sample / 65535.0) * 40)  # Notes entre 40 i 80
            velocity = 60 + int((sample / 65535.0) * 40)  # Velocitat entre 60 i 100
            
            # Aturar nota anterior si n'hi ha
            if hasattr(self, 'last_note'):
                self.midi_out.send(self.note_off(self.last_note, 0))
            
            # Reproduir nova nota
            self.midi_out.send(self.note_on(note, velocity))
            self.last_note = note
            
            # Actualitzar posició de reproducció
            self.last_play_pos = (self.last_play_pos + self.playback_speed) % self.buffer_size
        
        return {
            'mode': 'Màquina del Temps',
            'status': 'GRAVANT' if self.recording else 'REPRODUINT' if self.playing else 'INACTIU',
            'velocitat': f"{self.playback_speed:.1f}x",
            'degradació': f"{int(self.degradation*100)}%",
            'feedback': f"{int(self.feedback*100)}%"
        }
    
    def cleanup(self):
        self.recording = False
        self.playing = False
        
        # Aturar la nota actual si n'hi ha
        if hasattr(self, 'last_note'):
            self.midi_out.send(self.note_off(self.last_note, 0))
            
        return []
