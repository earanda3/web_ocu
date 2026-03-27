"""
Mode Ecos - Genera frases melòdiques que evolucionen amb el temps
"""
import time
import random
from modes.base_mode import BaseMode

class ModeEcosPasado(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Ecos"
        self.memory = []           # Emmagatzema patrons melòdics passats
        self.current_phrase = []    # Frase melòdica actual
        self.phase = 0              # Fase d'evolució
        self.last_note_time = 0     # Temps de l'última nota
        self.note_duration = 0.3    # Durada de cada nota en segons
        self.notes_playing = set()  # Notes actualment sonant
        
    def generate_melodic_pattern(self, x, y, z):
        """
        Genera un patró melòdic basat en els valors dels potenciòmetres
        """
        # Escales musicals
        scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'dorian': [0, 2, 3, 5, 7, 9, 10],
            'mixolydian': [0, 2, 4, 5, 7, 9, 10],
            'pentatonic': [0, 2, 4, 7, 9],
            'blues': [0, 3, 5, 6, 7, 10],
            'chromatic': list(range(12))
        }
        
        # Seleccionar escala basada en el potenciòmetre Y
        scale_idx = int((y / 127.0) * (len(scales) - 1))
        scale_name = list(scales.keys())[scale_idx]
        scale = scales[scale_name]
        
        # Longitud del patró (entre 3 i 12 notes)
        pattern_length = 3 + int((x / 127.0) * 9)
        
        # Generar patró melòdic
        pattern = []
        current_note = 60  # Nota base (Do central)
        
        for i in range(pattern_length):
            # Determinar direcció del moviment (ascendent, descendent o repetició)
            direction = random.choice([-1, 0, 1])
            
            # Ajustar la nota segons la direcció i l'escala
            if direction != 0:
                # Trobar índex actual a l'escala
                if current_note % 12 in scale:
                    current_scale_idx = scale.index(current_note % 12)
                else:
                    # Si la nota actual no està a l'escala, trobar la més propera
                    distances = [abs((current_note % 12) - note) for note in scale]
                    current_scale_idx = distances.index(min(distances))
                
                # Moure's dins de l'escala
                current_scale_idx = (current_scale_idx + direction) % len(scale)
                current_note = (current_note // 12) * 12 + scale[current_scale_idx]
                
                # Afegir salts d'octava ocasionals basats en el potenciòmetre Z
                if random.random() < (z / 200.0):  # Màxim 63.5% de probabilitat
                    current_note += 12 * random.choice([-1, 1])
            
            # Assegurar que la nota estigui en el rang MIDI (0-127)
            current_note = max(0, min(127, current_note))
            
            pattern.append(current_note)
        
        return pattern
    
    def evolve_pattern(self, pattern, creativity):
        """
        Evoluciona un patró existent amb un nivell de creativitat donat
        """
        if not pattern or random.random() > creativity:
            return pattern
            
        # Fer una còpia del patró
        new_pattern = pattern.copy()
        
        # Aplicar mutacions aleatòries
        mutation_type = random.choice(['transpose', 'invert', 'retrograde', 'rhythm', 'ornament'])
        
        if mutation_type == 'transpose' and len(new_pattern) > 0:
            # Transposar tot el patró
            steps = random.choice([-12, -7, -5, -3, -1, 1, 3, 5, 7, 12])
            new_pattern = [min(127, max(0, note + steps)) for note in new_pattern]
            
        elif mutation_type == 'invert' and len(new_pattern) > 1:
            # Invertir el patró al voltant de la primera nota
            first_note = new_pattern[0]
            new_pattern = [first_note + (first_note - note) for note in new_pattern]
            
        elif mutation_type == 'retrograde' and len(new_pattern) > 1:
            # Invertir l'ordre de les notes
            new_pattern = new_pattern[::-1]
            
        elif mutation_type == 'rhythm' and len(new_pattern) > 1:
            # Canviar el ritme (repetir o eliminar notes)
            if random.random() < 0.5 and len(new_pattern) < 12:
                # Duplicar una nota aleatòria
                idx = random.randint(0, len(new_pattern)-1)
                new_pattern.insert(idx, new_pattern[idx])
            elif len(new_pattern) > 3:
                # Eliminar una nota aleatòria
                idx = random.randint(0, len(new_pattern)-1)
                new_pattern.pop(idx)
                
        elif mutation_type == 'ornament' and len(new_pattern) > 1:
            # Afegir ornaments (notes de pas, mordents, etc.)
            idx = random.randint(0, len(new_pattern)-2)
            ornament_type = random.choice(['mordent', 'turn', 'appoggiatura'])
            
            if ornament_type == 'mordent':
                # Mordent: nota, nota superior, nota
                step = 1 if random.random() < 0.5 else -1
                new_note = new_pattern[idx] + step
                if 0 <= new_note <= 127:
                    new_pattern.insert(idx+1, new_note)
                    new_pattern.insert(idx+2, new_pattern[idx])
                    
            elif ornament_type == 'turn':
                # Grupet: nota superior, nota, nota inferior, nota
                upper = new_pattern[idx] + 1
                lower = new_pattern[idx] - 1
                if 0 <= upper <= 127 and 0 <= lower <= 127:
                    new_pattern.insert(idx+1, upper)
                    new_pattern.insert(idx+2, new_pattern[idx])
                    new_pattern.insert(idx+3, lower)
                    new_pattern.insert(idx+4, new_pattern[idx])
                    
            elif ornament_type == 'appoggiatura':
                # Apogiatura: nota de pas que resol a la nota principal
                step = 1 if random.random() < 0.5 else -1
                appoggiatura = new_pattern[idx] + step
                if 0 <= appoggiatura <= 127:
                    new_pattern.insert(idx, appoggiatura)
        
        return new_pattern
    
    def setup(self):
        self.initialized = True
        self.memory = []
        self.current_phrase = []
        self.phase = 0
        self.last_note_time = 0
        self.notes_playing = set()
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # Control de paràmetres amb potenciòmetres
        creativity = x / 127.0  # 0-1, controla la creativitat/aleatorietat
        memory_depth = max(1, int((y / 127.0) * 10))  # 1-10, quants patrons recordar
        evolution_speed = 0.1 + (z / 127.0) * 0.9  # 0.1-1.0, velocitat d'evolució
        
        # Actualitzar memòria
        if len(self.memory) > memory_depth:
            self.memory = self.memory[-memory_depth:]
        
        # Generar o evolucionar la frase actual
        if (not self.current_phrase or 
            current_time - self.last_note_time > self.note_duration):
            
            # Aturar notes actuals
            for note in self.notes_playing:
                self.midi_out.send(self.note_off(note, 0))
            self.notes_playing.clear()
            
            # Avançar fase
            self.phase += evolution_speed
            
            if random.random() < 0.3 * creativity:
                # Generar nou patró basat en la memòria
                if self.memory and random.random() < 0.7:
                    # Seleccionar i evolucionar un patró existent
                    source_pattern = random.choice(self.memory)
                    self.current_phrase = self.evolve_pattern(source_pattern, creativity)
                else:
                    # Generar nou patró
                    self.current_phrase = self.generate_melodic_pattern(x, y, z)
                
                # Afegir a la memòria
                self.memory.append(self.current_phrase.copy())
            
            # Reproduir la següent nota de la frase actual
            if self.current_phrase:
                note = self.current_phrase[int(self.phase) % len(self.current_phrase)]
                velocity = 100  # Velocitat fixa, es pot fer variable
                
                # Reproduir la nota
                self.midi_out.send(self.note_on(note, velocity))
                self.notes_playing.add(note)
                
                # Programar l'apagat de la nota
                # (en un entorn real, s'usaria un timer o un sistema d'esdeveniments)
                self.last_note_time = current_time
        
        return {
            'phase': self.phase,
            'memory_size': len(self.memory),
            'current_note': self.current_phrase[int(self.phase) % len(self.current_phrase)] if self.current_phrase else None,
            'creativity': creativity,
            'memory_depth': memory_depth,
            'evolution_speed': evolution_speed
        }
    
    def cleanup(self):
        # Aturar totes les notes en sortir del mode
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        return [(note, 0) for note in notes_to_stop]
