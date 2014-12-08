#JMPS = [NN_ja, NN_jnz, NN_jz, NN_js, NN_jg, NN_jle, NN_jl, NN_jnp, NN_jp, NN_jb, NN_jnb, NN_jbe, NN_jo, NN_jmp]
REGS = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
import idaapi
import idc
import IR
import IRCompiler
import FlowGraph
import Graph

def parse_mem(s):
    if s.specflag1:
        ret = IR.Const(s.addr)
        base  = s.specflag2 & 0x7
        index = (s.specflag2 & 0x38) >> 3
        scale = (s.specflag2 & 0xc0) >> 6
        if base != 5:
            ret = IR.Add(ret, IR.Var(REGS[base]))
        if index != 4:
            if scale > 0:
                ret = IR.Add(ret, IR.Mul(IR.Var(REGS[index]),IR.Const(2**scale)))
            else:    
                ret = IR.Add(ret, REGS[index])
        return ret        
    if s.addr:
        return IR.Add(IR.Var(REGS[s.phrase]), IR.Const(s.addr))  
    else:
        return IR.Var(REGS[s.phrase])

def decode_instr(eip):
    MakeCode(eip)
    mnem = idaapi.ua_mnem(eip)
    sz = idaapi.decode_insn(eip)
    x = dict(nextip=[],inst=mnem, ops=[])
    if not idaapi.cmd.itype in (idaapi.NN_jmp, idaapi.NN_retn):
        x['nextip'].append(eip+sz)
    for n, op in enumerate(idaapi.cmd.Operands):
        if op.type == 0: break
        ty = op.type
        text = idaapi.tag_remove(idaapi.ua_outop2(eip, n))
        if op.dtyp == 0:
            bits = 8
        elif op.dtyp == 1:    
            bits = 16
        elif op.dtyp == 2:    
            bits = 32

        if ty == idc.o_reg:
            x['ops'].append(IR.Var(text, bits))
        elif ty == idc.o_mem:
            x['ops'].append(IR.Mem(IR.Const(op.addr),bits))
        elif ty in (idc.o_phrase, idc.o_displ):
            x['ops'].append(IR.Mem(parse_mem(op),bits))
        elif ty == idc.o_imm:
            x['ops'].append(IR.Const(op.value,bits))
        elif ty == idc.o_near:
            x['ops'].append(IR.Const(op.addr))
            x['nextip'].append(op.addr)
        else:
            raise UnknownError
    return x
def compile_single(addr):
    decoded = decode_instr(addr)    
    opcode = str(decoded['inst'])
    if opcode in ('and','or','not'):
        opcode += "_" #THANKS OBAMA
    decoded['ir'] = getattr(IRCompiler,opcode)(*decoded['ops'])
    if len(decoded['ir']) > 0:
        decoded['ir'].insert(0,IR.Label("%08X" % addr))
        for s in decoded['ir']:
            s.asm = GetDisasm(addr) # TODO OPTIMIZE
    return decoded
def compile_function(addr):
    worklist = []
    visited = []
    g = FlowGraph.FlowGraph()
    entry = FlowGraph.BasicBlock(g)
    entry._id = addr
    g.entry = entry
    worklist.append(entry)
    while worklist:
        print visited
        current = worklist.pop()
        if current._id in visited:
            continue
        else:
            visited.append(current._id)
        decoded = compile_single(current._id)
        current.__dict__.update(decoded)
        for n in decoded['nextip']:
            if g.find_by_id(n):
                v = g.find_by_id(n)    
            else:    
                v = FlowGraph.BasicBlock(g)
                v._id = n
                worklist.append(v)
            g.add_edge(current, v)
    return g     
