"""
Mode Noise - Soroll crisp moderat, versio suau de HardNoise
X: Intensitat d'explosions
Y: Volum del fons greu
Z: Filtre sweep (CC74 Brightness)
Doble click: toggle CONTINU / RAFEGUES
"""
import time, random
from modes.base_mode import BaseMode
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange


class ModeNoise(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Noise"
        self.bg = [{'note':28,'vel':0,'on':False},{'note':32,'vel':0,'on':False}]
        self.playing = set()
        self.last_burst = self.last_mid = 0.0
        self.burst_int = self.bass_int = 0.3
        self.filter_val = 64
        self.burst_mode = False
        self.burst_cnt = self.burst_tot = 0
        self.last_release = [0.0]*16
        self.last_btn = [False]*16
        self.active_notes = []

    def setup(self):
        self.initialized = True
        self.playing = set()
        for b in self.bg: b['vel']=0; b['on']=False
        self.last_burst = self.last_mid = time.monotonic()
        self.last_release = [0.0]*16
        self.last_btn = [False]*16
        self.burst_cnt = 0
        try: self.midi_out.send(ControlChange(74, 64))
        except Exception: pass
        print(f"Noise: {'RAFEGUES' if self.burst_mode else 'CONTINU'}")

    def _bg(self):
        tgt = int(self.bass_int*50)
        for b in self.bg:
            b['vel'] = min(b['vel']+2,tgt) if b['vel']<tgt else max(b['vel']-2,tgt)
            n,v = b['note'],b['vel']
            try:
                if v>0 and not b['on']:
                    self.midi_out.send(NoteOn(n,v)); b['on']=True; self.playing.add(n)
                elif v==0 and b['on']:
                    self.midi_out.send(NoteOff(n,0)); b['on']=False; self.playing.discard(n)
                elif b['on']:
                    self.midi_out.send(NoteOn(n,v))
            except Exception: pass

    def _burst(self):
        for _ in range(1+int(self.burst_int*2)):
            n=random.randint(60,90); v=random.randint(55,100)
            try: self.midi_out.send(NoteOn(n,v)); self.playing.add(n)
            except Exception: pass

    def _decay(self):
        p=0.1+self.burst_int*0.1
        for n in [n for n in self.playing if n>=40 and random.random()<p]:
            try: self.midi_out.send(NoteOff(n,0)); self.playing.discard(n)
            except Exception: pass

    def update(self, pot_values, button_states):
        x,y,z = pot_values
        now = time.monotonic()
        self.burst_int = x/127.0; self.bass_int = y/127.0
        nf = int(z)
        if abs(nf-self.filter_val)>=2:
            self.filter_val=nf
            try: self.midi_out.send(ControlChange(74,nf))
            except Exception: pass
        self._bg(); self._decay()
        iv = max(0.08, 0.6-self.burst_int*0.5)
        if not self.burst_mode:
            if now-self.last_burst>iv: self._burst(); self.last_burst=now
        else:
            if self.burst_cnt<self.burst_tot:
                if now-self.last_burst>iv*0.5: self._burst(); self.last_burst=now; self.burst_cnt+=1
            else:
                if now-self.last_burst>max(0.3,1.0-self.burst_int*0.5):
                    self.burst_tot=random.randint(2,5); self.burst_cnt=0
        self.active_notes=list(self.playing)
        for i in range(min(len(button_states),16)):
            cur=bool(button_states[i])
            if self.last_btn[i] and not cur:
                gap=now-self.last_release[i]
                if 0.05<gap<0.4:
                    self.last_release[i]=0.0; self.burst_mode=not self.burst_mode
                    self.burst_cnt=0; print(f"Noise: {'RAFEGUES' if self.burst_mode else 'CONTINU'}")
                else: self.last_release[i]=now
            self.last_btn[i]=cur
        return {'mode':'BURST' if self.burst_mode else 'CONT','flt':self.filter_val}

    def stop(self): self.cleanup()

    def cleanup(self):
        for b in self.bg:
            if b['on']:
                try: self.midi_out.send(NoteOff(b['note'],0))
                except Exception: pass
            b['on']=False; b['vel']=0
        for n in list(self.playing):
            try: self.midi_out.send(NoteOff(n,0))
            except Exception: pass
        self.playing.clear(); self.active_notes=[]
        try:
            for ch in range(3):
                self.midi_out.send(ControlChange(123,0,channel=ch))
                self.midi_out.send(ControlChange(120,0,channel=ch))
            self.midi_out.send(ControlChange(74,64))
        except Exception: pass
