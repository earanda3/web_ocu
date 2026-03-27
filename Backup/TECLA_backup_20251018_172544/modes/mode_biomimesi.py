"""
Mode Biomímesi - Emula patrones biológicos como respiración, pulso y otros ritmos naturales
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeBiomimesi(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Biomímesi"
        self.active_notes = {}
        self.biological_cycles = []
        self.last_update = time.monotonic()
        
        # Escalas basadas en ratios naturales
        self.scales = {
            "fibonacci": [0, 1, 2, 3, 5, 8, 13, 21],
            "golden": [0, 3, 5, 7, 12, 15, 17, 19],
            "natural": [0, 2, 4, 7, 9, 12, 14, 16]
        }
        self.current_scale = "natural"
        
    def setup(self):
        self.initialized = True
        self.active_notes = {}
        self.last_update = time.monotonic()
        
        # Crear diferentes ciclos biológicos
        self.biological_cycles = [
            {"name": "respiración", "period": 3.0, "phase": 0, "base_note": 60, "channel": 0},
            {"name": "pulso", "period": 0.8, "phase": 0, "base_note": 48, "channel": 1},
            {"name": "nervioso", "period": 0.3, "phase": 0, "base_note": 72, "channel": 2},
            {"name": "digestivo", "period": 8.0, "phase": 0, "base_note": 36, "channel": 3},
            {"name": "circadiano", "period": 15.0, "phase": 0, "base_note": 24, "channel": 4}
        ]
    
    def _get_scale_note(self, base_note, step, scale_name):
        """Obtener una nota de la escala especificada"""
        scale = self.scales.get(scale_name, self.scales["natural"])
        octave = step // len(scale)
        scale_pos = step % len(scale)
        return base_note + scale[scale_pos] + (octave * 12)
        
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = min(0.1, current_time - self.last_update)
        self.last_update = current_time
        
        # Parámetros controlados por potenciómetros
        metabolism = 0.5 + (pot_values[0] / 127.0) * 2.0     # Velocidad metabólica (0.5x - 2.5x)
        complexity = (pot_values[1] / 127.0)                 # Complejidad biológica (0.0 - 1.0)
        evolution_rate = (pot_values[2] / 127.0)             # Tasa de evolución/mutación (0.0 - 1.0)
        
        # Seleccionar escala basada en complejidad
        if complexity < 0.33:
            self.current_scale = "natural"
        elif complexity < 0.66:
            self.current_scale = "golden"
        else:
            self.current_scale = "fibonacci"
        
        # Actualizar ciclos biológicos
        for cycle in self.biological_cycles:
            # Actualizar fase
            cycle["phase"] += dt * (1.0 / cycle["period"]) * metabolism
            cycle["phase"] %= 1.0
            
            # Calcular la forma de onda basada en el ciclo
            if cycle["name"] == "respiración":
                # Curva suave similar a la respiración
                waveform = 0.5 * (1 - math.cos(cycle["phase"] * 2 * math.pi))
            elif cycle["name"] == "pulso":
                # Pulso cardíaco (más pronunciado)
                x = cycle["phase"] * 2 * math.pi
                waveform = math.pow(math.sin(x) * 0.5 + 0.5, 2) if x < math.pi else 0.1
            elif cycle["name"] == "nervioso":
                # Impulsos nerviosos (esporádicos)
                waveform = 1.0 if cycle["phase"] < 0.1 else 0.0
            elif cycle["name"] == "digestivo":
                # Ciclo digestivo (ondas peristálticas)
                waveform = math.sin(cycle["phase"] * 2 * math.pi * 3) * 0.5 + 0.5
            else:  # circadiano
                # Ciclo circadiano (día/noche)
                waveform = math.sin(cycle["phase"] * 2 * math.pi) * 0.5 + 0.5
            
            # Introducir pequeñas mutaciones en el comportamiento basadas en evolution_rate
            if random.random() < evolution_rate * 0.01:
                # Pequeña variación en el período
                cycle["period"] *= random.uniform(0.95, 1.05)
                # Mantener el período dentro de límites razonables
                cycle["period"] = max(0.2, min(20.0, cycle["period"]))
            
            # Determinar si el ciclo debe generar una nota
            cycle_id = f"cycle_{id(cycle)}"
            trigger_threshold = 0.7 - (complexity * 0.4)  # Mayor complejidad = más notas
            
            # Si el ciclo supera el umbral de activación
            if waveform > trigger_threshold:
                # Calcular paso en la escala basado en la fase y complejidad
                step = int((cycle["phase"] * 8) + (complexity * 8))
                note = self._get_scale_note(cycle["base_note"], step, self.current_scale)
                
                # Velocidad basada en la forma de onda
                velocity = int(waveform * 100 + 27)  # Entre 27 y 127 para asegurar audibilidad
                
                # Si ya hay una nota activa para este ciclo con la misma nota, no hacer nada
                if cycle_id in self.active_notes and self.active_notes[cycle_id]["note"] == note:
                    continue
                
                # Detener la nota anterior si existe
                if cycle_id in self.active_notes:
                    try:
                        old_note = self.active_notes[cycle_id]["note"]
                        channel = cycle["channel"]
                        note_off_msg = self.note_off(old_note, 0)
                        note_off_msg.channel = channel
                        self.midi_out.send(note_off_msg)
                    except Exception as e:
                        print(f"Error al detener nota: {e}")
                
                # Tocar la nueva nota
                try:
                    note_on_msg = self.note_on(note, velocity)
                    note_on_msg.channel = cycle["channel"]
                    self.midi_out.send(note_on_msg)
                    self.active_notes[cycle_id] = {"note": note, "velocity": velocity}
                except Exception as e:
                    print(f"Error al tocar nota: {e}")
            elif cycle_id in self.active_notes:
                # Si el ciclo está por debajo del umbral y hay una nota activa, detenerla
                try:
                    old_note = self.active_notes[cycle_id]["note"]
                    channel = cycle["channel"]
                    note_off_msg = self.note_off(old_note, 0)
                    note_off_msg.channel = channel
                    self.midi_out.send(note_off_msg)
                    del self.active_notes[cycle_id]
                except Exception as e:
                    print(f"Error al detener nota: {e}")
        
        return {
            "mode": "Biomímesi",
            "metabolisme": f"{metabolism:.1f}x",
            "complexitat": f"{int(complexity * 100)}%",
            "evolució": f"{int(evolution_rate * 100)}%",
            "escala": self.current_scale
        }
    
    def cleanup(self):
        notes_to_stop = []
        
        # Detener todas las notas activas
        for cycle_id, note_data in self.active_notes.items():
            for cycle in self.biological_cycles:
                if f"cycle_{id(cycle)}" == cycle_id:
                    channel = cycle["channel"]
                    notes_to_stop.append([note_data["note"], 0, channel])
                    
                    # Enviar mensaje MIDI para detener la nota
                    try:
                        note_off_msg = self.note_off(note_data["note"], 0)
                        note_off_msg.channel = channel
                        self.midi_out.send(note_off_msg)
                    except Exception as e:
                        print(f"Error al limpiar nota: {e}")
        
        self.active_notes = {}
        return notes_to_stop
