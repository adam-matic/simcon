def parse_program_string( program_string ):

    def mtitle(p, line, items):
        p["title"] = line[ len(items[0]) + 1:]
    def mtime(p, line, items):
        p["duration"] = float(items[1])
        p["dt"] = float(items[2])
    def mgroup(p, line, items):
        p["groups"].append(items[1:])
    def mplot(p, line, items):
        p["plotx"] = items[1]
        p["plotys"] = items[2:]
    def mscale(p, line, items):
        p["scalex"] = float(items[1])
        p["scaleys"] = [float(i) for i in items[2:]]
    def mconst(p, line, items):
        p["const"] = {}
        for i in range(1, len(items), 2):
            p["const"][items[i]] = float(items[i+1])

    def remove_comments(line):
        i = line.find("#")
        if i == -1: return line
        return line[:i]

    store_command = {"title": mtitle, "time": mtime, "group": mgroup,
                     "plot":mplot, "scale": mscale, "const": mconst,
                     "begin": None, "end" : None}

    commands = list(store_command.keys())

    def msum(b, items):
        b["ins"] = items[2::2]
        b["ws"] = [float(i) for i in items[3::2]]

    def mintegrator(b, items):
        b["init_value"] = float(items[2])
        b["ins"] = items[3::2]
        b["ws"] = [float(i) for i in items[4::2]]

    def mamp(b, items):
        b["init_value"] = float(items[2])
        b["ins"] = [ items[3] ]
        b["K"]   = float(items[4])
        b["tc"]  = float(items[5])

    def mmult(b, items):  b["ins"] = items[2:]
    def mdiv(b, items):   b["ins"] = items[2:]
    def mcomp(b, items):  b["ins"] = items[2:]

    def mdelay(b, items): 
        b["ins"] = [ items[2] ]
        b["delay_time"] = float( items[3] )

    def mlimit(b, items):
        b["ins"] = [ items[2] ]
        b["low"] = float( items[3] )
        b["high"] = float( items[4] )

    def mfunc(b, items):
        elems = items[2:]
        b["xs"] = []
        b["ys"] = []
        for i in range(0, len(elems), 2):
            b["xs"].append(float(elems[i]))
            b["ys"].append(float(elems[i+1]))

    def mgen(b, items):
        ftype = items[2]
        b["ftype"] = ftype
        if ftype == "puls" or ftype == "ramp":
            b["start_time"] = float(items[3])
            b["end_time"] = float(items[4])
            b["amplitude"] = float(items[5])
        elif ftype == "random":
            b["tcs"] = [float(e) for e in items[3:]]

    def mconst2(b, items):
        b["init_value"] = float(items[2])

    make_block = {"summator": msum, "integrator": mintegrator,
                  "amplifier": mamp, "mult": mmult, "div": mdiv,
                  "comparator": mcomp, "delay": mdelay, 
                  "limit": mlimit, "func": mfunc, "generator": mgen,
                  "const": mconst2
                 }
    blocks = list(make_block.keys())

    program_dict = {"title" : "", "blocks": {}, "groups":[]}

    lines = program_string.split("\n")
    for line in lines:
        try:
            line = remove_comments(line)
            items = line.split()
            if len(items) <= 1: continue
            if items[0] in commands:
                store_command[items[0]](program_dict, line, items)
            elif items[1] in blocks:
                name = items[0]
                program_dict["blocks"][name] = {}
                block = program_dict["blocks"][name]
                block["type"] = items[1]
                block["ins"] = []
                make_block[items[1]](block, items)
            else:
                print("line ignored:", line)
        except Exception as e:
            print("Error in line:", line)
            print(e)
    
    pn = len(program_dict["plotys"])
    sn = len(program_dict.get("scaleys", []))
    if sn < pn: program_dict["scaleys"] = [1] * pn
    
    return program_dict