"""
Mode Industrial - Maquines, vapor, repeticio mecanica
"""
import time
from modes.base_mode import BaseMode

class ModeIndustrial(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Industrial"
        self.machine_step = 0
        self.last_step_time = 0
        self.steam_phase = 0
        
    def setup(self):
        self.initialized = True
        self.last_step_time = time.monotonic()
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        x, y, z = pot_values
        
        # X = Velocitat màquina (BPM mecànic)
        machine_bpm = 60 + int((x / 127.0) * 180)  # 60-240
        step_interval = 60.0 / (machine_bpm * 4)  # 16ths
        
        # Y = Vapor (pressió)
        steam_pressure = y / 127.0
        
        # Z = Complexitat màquina (engranatges)
        complexity = z / 127.0
        num_gears = 1 + int(complexity * 7)
        
        if current_time - self.last_step_time >= step_interval:
            # Màquina base (pols mecànic molt regular)
            if self.machine_step % 4 == 0:
                # Beat principal (fort)
                machine_note = 36
                machine_vel = 100
            elif self.machine_step % 2 == 0:
                # Beat secundari
                machine_note = 40
                machine_vel = 80
            else:
                # Tick mecànic
                machine_note = 48
                machine_vel = 60
            
            self.midi_out.send(self.note_on(machine_note, machine_vel))
            self.midi_out.send(self.note_off(machine_note, 0))
            
            # Engranatges (notes repetitives)
            for i in range(num_gears):
                if (self.machine_step + i) % (2 + i) == 0:
                    gear_note = 52 + (i * 4)
                    gear_vel = 70 - i * 5
                    self.midi_out.send(self.note_on(gear_note, max(40, gear_vel)))
                    self.midi_out.send(self.note_off(gear_note, 0))
            
            # Vapor (xiulet ocasional)
            if steam_pressure > 0.5:
                self.steam_phase += steam_pressure * 0.1
                if int(self.steam_phase) % int(10 / steam_pressure) == 0:
                    # Xiulet de vapor (agut)
                    steam_note = 84 + int(steam_pressure * 12)
                    steam_note = min(96, steam_note)
                    steam_vel = int(80 + steam_pressure * 40)
                    self.midi_out.send(self.note_on(steam_note, steam_vel))
                    self.midi_out.send(self.note_off(steam_note, 0))
            
            self.machine_step += 1
            self.last_step_time = current_time
        
        return {
            'machine': f"{machine_bpm} BPM",
            'steam': f"{int(steam_pressure * 100)}%",
            'gears': num_gears
        }
    
    def cleanup(self):
        return []
