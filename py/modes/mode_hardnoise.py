"""
Mode HardNoise - Soroll industrial extrem
X: Intensitat d'explosions agudes
Y: Volum del fons greu
Z: Velocitat general del caos
"""
import time, random
from modes.base_mode import BaseMode
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange


class ModeHardNoise(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name="HardNoise"
        self.bg=[
            {'note':24,'vel':0,'on':False},{'note':27,'vel':0,'on':False},
            {'note':31,'vel':0,'on':False},{'note':34,'vel':0,'on':False},
        ]
        self.playing=set()
        self.last_burst=self.last_mid=0.0
        self.burst_int=self.bass_int=self.chaos=0.5
        self.burst_mode=False
        self.burst_cnt=self.burst_tot=0
        self.active_notes=[]

    def setup(self):
        self.initialized=True;self.playing=set()
        for b in self.bg: b['vel']=0;b['on']=False
        self.last_burst=self.last_mid=time.monotonic();self.burst_cnt=0
        print(f"HardNoise: {'RAFEGUES' if self.burst_mode else 'CONTINU'}")

    def _bg(self):
        tgt=int(self.bass_int*70)
        for b in self.bg:
            b['vel']=min(b['vel']+3,tgt) if b['vel']<tgt else max(b['vel']-3,tgt)
            n,v=b['note'],b['vel']
            try:
                if v>0 and not b['on']: self.midi_out.send(NoteOn(n,v));b['on']=True;self.playing.add(n)
                elif v==0 and b['on']: self.midi_out.send(NoteOff(n,0));b['on']=False;self.playing.discard(n)
                elif b['on']: self.midi_out.send(NoteOn(n,v))
            except Exception: pass

    def _burst(self, t):
        for _ in range(1+int(self.burst_int*3)):
            n=random.randint(80,110);v=random.randint(90,127)
            try: self.midi_out.send(NoteOn(n,v));self.playing.add(n)
            except Exception: pass

    def _mid(self, t):
        n=random.randint(45,70);v=int(60+self.chaos*50)
        try: self.midi_out.send(NoteOn(n,v));self.playing.add(n)
        except Exception: pass

    def _decay(self):
        p=0.08+self.chaos*0.15
        for n in [n for n in self.playing if n>=40 and random.random()<p]:
            try: self.midi_out.send(NoteOff(n,0));self.playing.discard(n)
            except Exception: pass

    def update(self, pot_values, button_states):
        x,y,z=pot_values;now=time.monotonic()
        self.burst_int=x/127.0;self.bass_int=y/127.0;self.chaos=z/127.0
        self._bg();self._decay()
        iv=max(0.03,0.5-self.burst_int*0.47)
        if not self.burst_mode:
            if now-self.last_burst>iv: self._burst(now);self.last_burst=now
        else:
            pd=max(0.2,0.8-self.chaos*0.6)
            if self.burst_cnt<self.burst_tot:
                if now-self.last_burst>iv*0.4: self._burst(now);self.last_burst=now;self.burst_cnt+=1
            else:
                if now-self.last_burst>pd: self.burst_tot=random.randint(3,8);self.burst_cnt=0
        mi=max(0.1,1.0-self.burst_int*0.8)
        if now-self.last_mid>mi:
            if random.random()<(0.3+self.burst_int*0.5): self._mid(now)
            self.last_mid=now
        self.active_notes=list(self.playing)
        return {'mode':'BURST' if self.burst_mode else 'CONT'}

    def stop(self): self.cleanup()

    def cleanup(self):
        for b in self.bg:
            if b['on']:
                try: self.midi_out.send(NoteOff(b['note'],0))
                except Exception: pass
            b['on']=False;b['vel']=0
        for n in list(self.playing):
            try: self.midi_out.send(NoteOff(n,0))
            except Exception: pass
        self.playing.clear();self.active_notes=[]
        try:
            for ch in range(3):
                self.midi_out.send(ControlChange(123,0,channel=ch))
                self.midi_out.send(ControlChange(120,0,channel=ch))
            self.midi_out.send(ControlChange(64,0))
        except Exception: pass
