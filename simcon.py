from math import sin, pi
import matplotlib.pyplot as plt
import numpy as np
from string_parser import parse_program_string

class Block():
    def __init__(self, init_value=0, ins = []):
        self.state = init_value
        self.ins = ins
        self.next_state = init_value
        self.history = []
    def step(self): pass
    def advance(self):
        self.history.append(self.state)
        self.state = self.next_state

class Integrator(Block):
    def __init__(self, init_value=0, ins=[], ws=[], dt=0.001):
        super().__init__(init_value=init_value, ins=ins)
        self.dt = dt
        self.ws = ws
        self.old_input = init_value # sum([i.state for i in self.ins])
        
    def step(self):
        N = len(self.ins)
        sum_of_inputs = sum([self.ins[i].state * self.ws[i] for i in range(N)])
        self.next_state = self.state + (self.old_input + sum_of_inputs) * (self.dt / 2)
        self.old_input = sum_of_inputs

class Const(Block):
    def __init__(self, init_value=1): 
        super().__init__(init_value=init_value)
        
class Sine(Block):
    def step(self):
        t = self.ins[0].state
        f = self.ins[1].state
        self.next_state = sin ( 2 * pi * t * f)

class Counter(Block):
    def step(self): self.next_state = self.state + 1

class Time(Block):
    def __init__(self, init_value=0, dt = 0.001):
        super().__init__(init_value, dt)
    def step(self): self.next_state = self.state + self.dt
    
class Amplifier(Block):
    def __init__(self, init_value=0, K=50, tc=0.51, ins=[], limits = None, dt=0.001):
        super().__init__(init_value=init_value, ins=ins)
        self.dt = dt
        self.K = K
        self.tc = tc
        self.limits = limits

    def step(self):
        i = self.ins[0].state
        s = self.state
        self.next_state = s + (self.K * i - s) * (self.dt / self.tc)             
        
        if self.limits is not None:
            if self.next_state < self.limits[0]: self.next_state = self.limits[0]
            if self.next_state > self.limits[1]: self.next_state = self.limits[1]
            
class Comparator(Block):        
    def step(self):
        a = self.ins[0].state
        b = self.ins[1].state
        self.next_state = a - b

class Summator(Block):
    def __init__(self, ins=[], ws=[]):
        self.ins = ins
        self.ws = ws
        super().__init__(ins = ins)
    def step(self):
        N = len(self.ins)
        self.next_state = sum([self.ins[i].state * self.ws[i] for i in range(N)])
        
class Delay(Block):
    def __init__(self, delay_time=1, ins=[], dt = 0.001):
        super().__init__(ins=ins, init_value = 0)
        self.delay_time = delay_time
        self.delay_units = int(self.delay_time / dt)
        self.ys = [self.state] * self.delay_units
        
    def step(self):
        self.ys.append(self.ins[0].state)
        self.next_state = self.ys[ -self.delay_units ]        

class Limit(Block):
    def __init__(self, high=0, low=1, ins = []):
        super().__init__(ins=ins)
        self.minv = low
        self.maxv = high
    def step(self):
        x = self.ins[0].state
        if x > self.maxv: x = self.maxv
        elif x < self.minv: x = self.minv
        self.next_state = x
        
class Mult(Block):
    def step(self):
        a = self.ins[0].state
        b = self.ins[0].state
        self.next_state = a * b

class Div(Block):
    def step(self):
        a = self.ins[0].state
        b = self.ins[0].state
        self.next_state = a / b

class Func(Block):
    def __init__(self, xs=[], ys=[], dt=0.001, duration=1):
        super().__init__()
        imax = int(duration/dt)
        ts = [i * dt for i in range(imax)]
        if xs[0] > 0:
            xs = [0] + xs
            ys = [0] + ys
        if xs[-1] < duration:
            xs.append(duration)
            ys.append(0)
        i, j = 0, 0
        self.ys = [ys[0]]
        for j in range(len(xs) - 1):
            dys = ys[j+1] - ys[j]
            dxs = xs[j+1] - xs[j]
            ch = (dys/dxs) * dt
            while i < imax and ts[i] <= xs[j+1] :
                self.ys.append(self.ys[-1] + ch )
                i += 1
        self.counter = 0
        #print(len(self.ys), imax, "this is same?")
    
    def step(self):
        self.next_state = self.ys[self.counter]
        self.counter += 1

class Generator(Block):
    def __init__(self, ftype, start_time=0, end_time=1, amplitude=1, ins=[], duration =1, dt = 0.001, tcs = []):
        super().__init__()
        self.counter = 0
        imax = int(duration / dt)
        if ftype in ["puls", "ramp"]: 
            i0 = int(start_time / dt) 
            i1 = int(end_time / dt) 
            on_time =  (end_time - start_time)
            dy = (amplitude / on_time) * dt
            if ftype=="puls":
                self.ys = [ amplitude if (i >= i0 and i <= i1) else 0 for i in range(imax) ]
            elif ftype == "ramp":
                dys = [ dy if (i >= i0 and i <= i1) else 0 for i in range (imax) ]
                self.ys = np.cumsum(dys)
        elif ftype in ["random"]:
            import random
            y = 0; ys = [0]
            for i in range(imax):
                y = y +  (0.002 * (random.random() * 1000 - 500)) * dt / tcs[0]                
                for tc in tcs[1:]: y += (y - ys[-1]) * dt / tc
                ys.append(y)
            self.ys = ys
        
    def step(self):
        self.next_state = self.ys[self.counter]
        self.counter += 1
    
    
block_classes = {"summator": Summator, "integrator": Integrator,
                  "amplifier": Amplifier, "mult": Mult, "div": Div,
                  "comparator": Comparator, "delay": Delay, 
                  "limit": Limit, "func": Func, "generator": Generator,
                  "const": Const }

class AnalogComputer():
    def __init__(self, program, debug=False):
        if type(program) == type("text"):
            program = parse_program_string(program)
        if debug: print(program)
        
        self.program = program
        self.title = program["title"]
        self.dt = program["dt"]
        self.duration = program["duration"]
        self.plotx = program["plotx"]
        self.plotys = program["plotys"]
        self.scaleys = program["scaleys"]
        self.groups = program["groups"]
        self.blocks = {}
        names = list(program["blocks"].keys())
        for name in names:
            params = program["blocks"][name]
            btype = params["type"]
            params.pop("type", None)
            #print(name, btype)
            if btype in ["integrator", "amplifier", "generator", "func", "delay"]: params["dt"] = self.dt
            if btype in ["generator", "func"]: params["duration"] = self.duration
            if btype in ["generator", "const", 'func']: params.pop("ins", None)
            #print(params)
            bk = block_classes[btype](**params)
            bk.output_label = name
            self.blocks[name] = bk
            
            
        for b, v in self.blocks.items():
            v.ins = [self.blocks[n] for n in v.ins]
        
    def reset(self):
        self.__init__(self.program)
        
    def run(self):
        total_steps = int(self.duration / self.dt)
        
        all_signals = set(self.blocks.keys())
        groups = self.groups
        
        for g in groups: all_signals.difference_update(g)
        for el in all_signals: groups.append([el])

        def run_group(group):
            for element in group:
                self.blocks[element].step()
                self.blocks[element].advance()
                
        for s in range(total_steps):
            for g in groups: run_group(g)                
        
        return self
        
    def plot(self, signals=[], scales=[]):
        x = [i * self.dt for i in range(int(self.duration/ self.dt)) ]        
        if signals == []:
            ys = [ self.blocks[y].history for y in self.plotys ]
            labels = self.plotys
        else:
            ys = [ self.blocks[y].history for y in signals ]            
            labels = signals
            
        for i in range(len(ys)):
            k = self.scaleys[i]
            y = [yk * k for yk in ys[i]]
            plt.plot(x, y, label=labels[i])
        plt.title(self.title)
        plt.legend()
        plt.xlabel("time (s)")
        plt.show()
        return self