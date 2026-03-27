"""
Mode Harmonia Celeste - Simulación musical de las órbitas planetarias
Basado en el concepto pitagórico de la "música de las esferas"
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModeHarmoniaCeleste(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Harmonia Celeste"
        self.active_notes = {}
        self.orbits = []
        self.last_update = time.monotonic()
        self.scale = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24]  # Escala pentatónica extendida
        
    def setup(self):
        self.initialized = True
        self.active_notes = {}
        self.last_update = time.monotonic()
        
        # Crear diferentes órbitas planetarias
        self.orbits = [
            {"period": 0.5, "phase": 0, "base_note": 48, "radius": 1},    # Mercurio
            {"period": 1.2, "phase": 0.2, "base_note": 52, "radius": 2},  # Venus
            {"period": 2.0, "phase": 0.4, "base_note": 55, "radius": 3},  # Tierra
            {"period": 3.7, "phase": 0.6, "base_note": 59, "radius": 4},  # Marte
            {"period": 11.8, "phase": 0.8, "base_note": 43, "radius": 6}, # Júpiter
            {"period": 29.4, "phase": 1.0, "base_note": 38, "radius": 8}  # Saturno
        ]
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = min(0.1, current_time - self.last_update)
        self.last_update = current_time
        
        # Parámetros controlados por potenciómetros
        tempo_mod = 0.5 + (pot_values[0] / 127.0) * 2.0      # Modificador de tempo (0.5x - 2.5x)
        harmony_density = (pot_values[1] / 127.0)            # Densidad armónica (0.0 - 1.0)
        resonance = 0.3 + (pot_values[2] / 127.0) * 0.7      # Resonancia (0.3 - 1.0)
        
        # Actualizar las órbitas y generar notas
        for orbit in self.orbits:
            # Actualizar fase
            orbit["phase"] += dt * (1.0 / orbit["period"]) * tempo_mod
            orbit["phase"] %= 1.0  # Mantener entre 0 y 1
            
            # Determinar si el planeta debe sonar en este momento
            harmonic_point = (math.sin(orbit["phase"] * 2 * math.pi) + 1) / 2
            
            # Calcular la nota basada en la posición orbital
            note_offset = int(harmonic_point * len(self.scale))
            note = orbit["base_note"] + self.scale[note_offset % len(self.scale)]
            
            # Calcular la velocidad (volumen) basada en la resonancia
            velocity = int(((math.sin(orbit["phase"] * 2 * math.pi) + 1) / 2) * 127 * resonance)
            
            # Decidir si tocar la nota basado en la densidad armónica
            trigger_threshold = 1.0 - (harmony_density * 0.8)  # Más densidad = más notas
            
            orbit_id = f"orbit_{id(orbit)}"
            
            # Si el planeta cruza el "ecuador" y supera el umbral de densidad, emitir nota
            if (harmonic_point > 0.95 or harmonic_point < 0.05) and random.random() > trigger_threshold:
                # Detener la nota anterior si existe
                if orbit_id in self.active_notes:
                    try:
                        old_note = self.active_notes[orbit_id]["note"]
                        channel = self.active_notes[orbit_id]["channel"]
                        note_off_msg = self.note_off(old_note, 0)
                        note_off_msg.channel = channel
                        self.midi_out.send(note_off_msg)
                    except Exception as e:
                        print(f"Error al detener nota: {e}")
                
                # Asignar un canal basado en el planeta (para timbres diferentes)
                channel = orbit["radius"] % 16
                
                # Tocar la nueva nota
                try:
                    note_on_msg = self.note_on(note, velocity)
                    note_on_msg.channel = channel
                    self.midi_out.send(note_on_msg)
                    self.active_notes[orbit_id] = {"note": note, "velocity": velocity, "channel": channel}
                except Exception as e:
                    print(f"Error al tocar nota: {e}")
        
        return {
            "mode": "Harmonia Celeste",
            "tempo": f"{tempo_mod:.1f}x",
            "densidad": f"{int(harmony_density * 100)}%",
            "resonancia": f"{int(resonance * 100)}%"
        }
    
    def cleanup(self):
        notes_to_stop = []
        
        # Detener todas las notas activas
        for orbit_id, note_data in self.active_notes.items():
            notes_to_stop.append([note_data["note"], 0, note_data["channel"]])
            
            # Enviar mensaje MIDI para detener la nota
            try:
                note_off_msg = self.note_off(note_data["note"], 0)
                note_off_msg.channel = note_data["channel"]
                self.midi_out.send(note_off_msg)
            except Exception as e:
                print(f"Error al limpiar nota: {e}")
        
        self.active_notes = {}
        return notes_to_stop
