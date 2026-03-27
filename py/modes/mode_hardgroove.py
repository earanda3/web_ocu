"""
Mode HardGroove - Groove ritmic amb swing i half-time
X: Tempo (BPM: 90-160)
Y: Patró (Breakbeat, Shuffle, Funky, Crunk)
Z: Breakdown (0=kick, 32=+snare, 64=+hh, 96=full)
"""
import time
from modes.base_mode import BaseMode
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

_KICK=36;_SNARE=38;_CLAP=39;_HH=42;_OH=46
_BASS=(36,37,38,39,40,41,42,43,44,45,46,47)
_PATTERNS=(
    ((1,0,1,0,90),(0,0,0,0,0),(0,0,1,0,0),(0,1,0,0,0),
     (0,0,1,0,0),(1,0,0,0,70),(0,0,1,0,0),(0,0,0,1,0),
     (1,0,1,0,90),(0,0,0,0,0),(0,1,1,0,0),(1,0,0,0,60),
     (0,0,1,0,0),(0,0,0,0,0),(1,1,0,0,0),(0,0,1,0,50)),
    ((1,0,0,0,100),(0,0,1,0,0),(0,0,0,0,70),(0,1,0,0,0),
     (0,0,1,0,0),(1,0,0,0,80),(0,0,1,0,0),(0,0,0,0,0),
     (1,0,0,0,100),(0,0,1,0,0),(0,0,0,0,70),(0,1,0,0,0),
     (0,0,1,0,0),(1,0,0,1,80),(0,0,1,0,0),(0,0,0,0,60)),
    ((1,0,1,0,95),(0,0,0,0,0),(0,0,1,0,65),(1,0,0,0,80),
     (0,1,1,0,0),(0,0,0,0,0),(1,0,1,0,75),(0,0,0,0,55),
     (1,0,1,0,95),(0,1,0,0,0),(0,0,1,0,65),(0,0,0,1,0),
     (0,1,1,0,0),(1,0,0,0,0),(0,0,1,0,75),(0,0,0,0,55)),
    ((1,0,0,0,127),(0,0,1,0,0),(0,0,0,0,0),(0,0,1,0,0),
     (0,1,0,0,0),(0,0,1,0,0),(1,0,0,0,90),(0,0,1,0,0),
     (1,0,0,0,127),(0,1,0,0,0),(0,0,0,0,0),(0,0,1,0,0),
     (0,0,0,1,0),(0,0,1,0,0),(1,1,0,0,90),(0,0,1,0,100)),
)
_PNAMES=('Break','Shuffle','Funky','Crunk')
_GATE=0.05;_BG=0.4


def _on(m,n,v,c):
    try: msg=NoteOn(n&0x7F,max(1,min(127,v))&0x7F);msg.channel=c;m.send(msg)
    except Exception: pass
def _off(m,n,c):
    try: msg=NoteOff(n&0x7F,0);msg.channel=c;m.send(msg)
    except Exception: pass
def _cc(m,c,v,ch):
    try: msg=ControlChange(c,max(0,min(127,v))&0x7F);msg.channel=ch;m.send(msg)
    except Exception: pass


class ModeHardGroove(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name="HardGroove"
        self.bpm=120.0;self.pattern_idx=0;self.key_idx=0
        self.step=0;self.step_dur=0.0;self.last_step_t=0.0
        self.ak=False;self.ak_t=0.0;self.as_=False;self.as_t=0.0
        self.ah=False;self.ah_t=0.0;self.ab=False;self.ab_t=0.0
        self.layer=3
        self.active_notes=[]

    def setup(self):
        self.initialized=True;self.step=0;self._calc()
        self.last_step_t=time.monotonic()
        _cc(self.midi_out,123,0,9);_cc(self.midi_out,123,0,0)
        print(f"HardGroove: {_PNAMES[self.pattern_idx]} {int(self.bpm)}BPM")

    def _calc(self): self.step_dur=60.0/self.bpm/4.0

    def _release(self, now):
        if self.ak and now-self.ak_t>=_GATE: _off(self.midi_out,_KICK,9);self.ak=False
        if self.as_ and now-self.as_t>=_GATE: _off(self.midi_out,_SNARE,9);_off(self.midi_out,_CLAP,9);self.as_=False
        if self.ah and now-self.ah_t>=_GATE: _off(self.midi_out,_HH,9);_off(self.midi_out,_OH,9);self.ah=False
        if self.ab and now-self.ab_t>=self.step_dur*_BG: _off(self.midi_out,_BASS[self.key_idx],0);self.ab=False

    def _fire(self, s, now):
        k,sn,h,o,bv=s;v=100;L=self.layer
        if k: _on(self.midi_out,_KICK,min(127,int(v*1.2)),9);self.ak=True;self.ak_t=now
        if sn and L>=1: _on(self.midi_out,_SNARE,min(127,int(v*1.1)),9);_on(self.midi_out,_CLAP,max(1,int(v*0.8)),9);self.as_=True;self.as_t=now
        if h and L>=2: _on(self.midi_out,_HH,max(1,int(v*0.7)),9);self.ah=True;self.ah_t=now
        if o and L>=2: _on(self.midi_out,_OH,max(1,int(v*0.9)),9);self.ah=True;self.ah_t=now
        if bv>0: _on(self.midi_out,_BASS[self.key_idx],max(1,min(127,bv)),0);self.ab=True;self.ab_t=now

    def update(self, pot_values, button_states):
        x,y,z=pot_values;now=time.monotonic()
        nb=90.0+(x/127.0)*70.0
        if abs(nb-self.bpm)>0.5: self.bpm=nb;self._calc()
        np=min(3,int((y/127.0)*4))
        if np!=self.pattern_idx: self.pattern_idx=np;self.step=0;print(f"HardGroove: {_PNAMES[self.pattern_idx]}")
        # Z: Breakdown (0=kick, 1=+snare, 2=+hh, 3=full)
        self.layer=min(3,int((z/127.0)*4))
        self._release(now)
        if now-self.last_step_t>=self.step_dur:
            self.last_step_t=now;self._fire(_PATTERNS[self.pattern_idx][self.step],now)
            self.step=(self.step+1)%16
        _LNAMES=('KICK','KICK+SN','FULL-','FULL')
        return {'bpm':int(self.bpm),'pat':_PNAMES[self.pattern_idx],'lay':_LNAMES[self.layer]}

    def stop(self): self.cleanup()

    def cleanup(self):
        for n in (_KICK,_SNARE,_CLAP,_HH,_OH): _off(self.midi_out,n,9)
        _off(self.midi_out,_BASS[self.key_idx],0)
        _cc(self.midi_out,123,0,9);_cc(self.midi_out,123,0,0)
        _cc(self.midi_out,120,0,9);_cc(self.midi_out,120,0,0)
        self.ak=self.as_=self.ah=self.ab=False
