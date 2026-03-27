"""
Mode Veus - Genera patrons rítmics basats en fractals del conjunt de Mandelbrot
amb veus i textures sonores
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeVeus(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Veus"
        self.last_update = time.monotonic()
        self.notes_playing = set()
        
        # Paràmetres del fractal
        self.scale = 0.5  # Escala del fractal
        self.offset_x = -0.5  # Desplaçament X
        self.offset_y = 0.0   # Desplaçament Y
        self.max_iter = 10    # Iteracions màximes
        self.threshold = 4    # Llindar per a la convergència
        
        # Paràmetres musicals
        self.base_note = 36  # C2 - Nota base más grave para kicks potentes
        self.velocity = 127  # Velocitat màxima per a més impacte
        self.octave_range = 1  # Menys variació d'octaves per a un so més consistent
        self.note_duration = 0.15  # Durada lleugerament més llarga per a més presència
        self.velocity_variation = 0.3  # Variació de velocitat per a més dinàmica
        
        # Estat intern
        self.pattern = []
        self.pattern_index = 0
        self.last_note_time = 0
        self.last_pattern_update = time.monotonic()
        self.bpm = 120
        self.note_interval = 60.0 / (self.bpm * 4)  # Semicorxeres per defecte
        
        # Generar el patró inicial
        self._generate_pattern()
    
    def setup(self):
        """Inicialitza l'estat del mode."""
        self.initialized = True
        self._update_interval()
        print(f"Mode Veus iniciat. BPM: {self.bpm}")
    
    def _update_interval(self):
        """Actualitza l'interval entre notes segons el BPM."""
        self.note_interval = 60.0 / (self.bpm * 4)  # Semicorxeres
    
    def _mandelbrot(self, c, max_iter):
        """Calcula el valor de Mandelbrot per un punt complex c."""
        z = 0
        n = 0
        while abs(z) < self.threshold and n < max_iter:
            z = z*z + c
            n += 1
        return n
    
    def _generate_pattern(self):
        """Genera un nou patró fractal."""
        self.pattern = []
        width, height = 4, 4  # Matriu 4x4 pels 16 botons
        
        for y in range(height):
            for x in range(width):
                # Mapejar coordenades a l'espai del fractal
                zx = self.scale * (x / width - 0.5) + self.offset_x
                zy = self.scale * (y / height - 0.5) + self.offset_y
                
                # Calcular valor de Mandelbrot
                c = complex(zx, zy)
                val = self._mandelbrot(c, self.max_iter)
                
                # Mapejar el valor a una nota MIDI (0-15 per a 16 botons)
                note = self.base_note + (val % (self.octave_range * 12))
                
                # Afegir al patró amb una probabilitat basada en la posició
                if val < self.max_iter:  # Dins del conjunt de Mandelbrot
                    self.pattern.append((note, self.velocity, self.note_duration))
                else:
                    self.pattern.append(None)  # Silenci
        
        print(f"Patró fractal generat amb {len([x for x in self.pattern if x])} notes actives")
    
    def update(self, pot_values, button_states):
        """Actualitza l'estat del mode basat en els potenciòmetres."""
        current_time = time.monotonic()
        
        # Inicialitzar el diccionari d'estat
        status = {
            'mode': self.name,
            'bpm': self.bpm,
            'base_note': self.base_note,
            'scale': self.scale
        }
        
        # Actualitzar paràmetres basats en els potenciòmetres
        if len(pot_values) >= 3:
            # Potenciòmetre 1: Controla l'escala del fractal (zoom in/out)
            self.scale = 0.1 + (pot_values[0] / 127.0) * 1.9  # 0.1 a 2.0
            
            # Potenciòmetre 2: Controla la velocitat (BPM)
            self.bpm = 40 + int((pot_values[1] / 127.0) * 160)  # 40 a 200 BPM
            self._update_interval()
            
            # Potenciòmetre 3: Controla la nota base (pitch) - Rang més greu
            # Mapejar de 0-127 a un rang d'1.5 octaves (18 semitonos) a partir de C1 (24) fins a A2 (45)
            self.base_note = 24 + int((pot_values[2] / 127.0) * 18)  # C1 a A2 (24 a 45)
            
            # Ajustos addicionals basats en la posició del fractal
            # Utilitzem els valors dels potenciòmetres per canviar la posició
            # Això permet explorar diferents zones del fractal
            self.offset_x = -0.8 + (pot_values[1] / 127.0) * 0.6  # -0.8 a -0.2
            self.offset_y = -0.4 + ((pot_values[0] + pot_values[2]) / 254.0) * 0.8  # -0.4 a 0.4 (combinació de pot1 i pot3)
            
            # Regenerar el patró si algun paràmetre ha canviat significativament
            if current_time - self.last_pattern_update > 0.2:  # Limit de 5 actualitzacions/segon
                self._generate_pattern()
                self.last_pattern_update = current_time
        
        # Reproduir el patró
        if current_time - self.last_note_time >= self.note_interval:
            self.last_note_time = current_time
            
            # Aturar notes actuals
            for note in list(self.notes_playing):
                self.midi_out.send(self.note_off(note, 0))
                self.notes_playing.remove(note)
            
            # Reproduir següent nota del patró si n'hi ha
            if self.pattern:
                note_info = self.pattern[self.pattern_index]
                if note_info:
                    note, velocity, _ = note_info
                    # Aplicar variació de velocitat per a més dinàmica
                    varied_velocity = max(80, min(127, int(velocity * (1.0 + (random.random() * self.velocity_variation - self.velocity_variation/2)))))
                    # Asegurar que las notas estén en el rango MIDI (0-127)
                    safe_note = max(12, min(60, note))  # Limitar a un rango seguro para kicks
                    self.midi_out.send(self.note_on(safe_note, varied_velocity))
                    self.notes_playing.add(safe_note)
                
                # Actualitzar índex per a la següent nota
                self.pattern_index = (self.pattern_index + 1) % len(self.pattern)
        
        # Actualitzar l'estat amb els valors actuals
        status.update({
            'bpm': self.bpm,
            'base_note': self.base_note,
            'scale': self.scale
        })
        
        return status
    
    def cleanup(self):
        """Atura totes les notes en sortir del mode."""
        notes_to_stop = []
        for note in list(self.notes_playing):
            self.midi_out.send(self.note_off(note, 0))
            notes_to_stop.append([note, 0, 0])
        self.notes_playing.clear()
        print("Mode Veus aturat")
        return notes_to_stop
