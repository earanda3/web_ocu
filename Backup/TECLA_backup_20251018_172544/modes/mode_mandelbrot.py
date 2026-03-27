"""
Mode Mandelbrot - Genera sons basats en el conjunt de Mandelbrot
"""
import math
import random
from modes.base_mode import BaseMode

class ModeMandelbrot(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Mandelbrot"
        self.iteration = 0
        self.notes_playing = set()
        
    def mandelbrot_to_midi(self, cx, cy, max_iter=100):
        """
        Versió optimitzada del càlcul de Mandelbrot per a generació MIDI.
        Usa aritmètica de nombres enters per a millor rendiment.
        """
        # Escalar les entrades per a obtenir valors interessants al conjunt de Mandelbrot
        x0 = (cx / 127.0) * 3.5 - 2.5
        y0 = (cy / 127.0) * 2.0 - 1.0
        
        x = 0.0
        y = 0.0
        iteration = 0
        
        # Optimització: usar aritmètica de nombres enters per a millor rendiment
        x_sq = 0.0
        y_sq = 0.0
        
        while (x_sq + y_sq <= 4.0) and (iteration < max_iter):
            y = (x + x) * y + y0
            x = x_sq - y_sq + x0
            x_sq = x * x
            y_sq = y * y
            iteration += 1
        
        # Mapejar el nombre d'iteracions a una nota MIDI (0-127)
        if iteration == max_iter:
            return 0  # Dins del conjunt de Mandelbrot
        else:
            # Escalar de manera no lineal y asegurar que esté en el rango 0-127
            note = int((iteration / max_iter) ** 0.5 * 127)
            return max(0, min(127, note))  # Asegurar que esté en el rango 0-127
    
    def setup(self):
        self.initialized = True
        self.iteration = 0
        self.notes_playing = set()
    
    def update(self, pot_values, button_states):
        x, y, z = pot_values
        
        # Actualitzar iteració per a animació
        self.iteration += 1
        
        # Generar nota basada en la posició dels potenciòmetres
        note = self.mandelbrot_to_midi(x, y)
        
        # Si s'ha generat una nota vàlida
        if note > 0:
            # Aturar notes anteriors
            for n in list(self.notes_playing):
                self.midi_out.send(self.note_off(n, 0))
            self.notes_playing.clear()
            
            # Reproduir nova nota si está en rango
            if 0 <= note <= 127:
                velocity = min(127, max(0, int(z * 1.5)))  # Asegurar velocidad en rango
                self.midi_out.send(self.note_on(note, velocity))
                self.notes_playing.add(note)
        
        return {
            'note': note if note > 0 else None,
            'x': x,
            'y': y,
            'z': z
        }
    
    def cleanup(self):
        # Aturar totes les notes en sortir del mode
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        return [(note, 0) for note in notes_to_stop]
