from IR import *
High24 = Const(0xffffff00)
High16Low8 = Const(0xffff00ff)
High16 = Const(0xffff0000)
Low16 =  Const(0x0000ffff)
High8 = Const(0xff00)
Low8 =  Const(0x00ff)

def assigns_op(op=1,reg=None):
    def wrap(f):
        def wrapper(*args):
            res = f(*args)
            if reg:
                o1 = reg
            else:
                o1 = args[op-1]
            if not isinstance(o1, Var):
                return res # Not a register
            op1 = o1.name
            if op1 in ('eax', 'ebx', 'ecx', 'edx','esi', 'edi', 'ebp', 'esp'):
                bit16 = Var(op1[1]+op1[2])
                bitl8 = Var(op1[1]+'l')
                bith8 = Var(op1[1]+'h')
                res.append(Move(bit16, And(o1, Low16)))
                if op1 in ('eax', 'ebx', 'ecx', 'edx'):
                    res.append(Move(bitl8,And(o1,Low8)))
                    tmp = Temp()
                    res.append(Move(tmp,And(o1,High8)))
                    res.append(Move(bith8,RShift(tmp,Const(8))))
            elif op1 in ('ax','bx', 'cx', 'dx'):
                    bit32 = Var('e'+op1)
                    bitl8 = Var(op1[0]+'l')
                    bith8 = Var(op1[0]+'h')
                    tmp1 = Temp()
                    tmp2 = Temp()
                    res.append(Move(tmp1,And(bit32, High16)))
                    res.append(Move(bit32,Or(tmp1,o1)))
                    res.append(Move(bitl8,And(o1,Low8)))
                    res.append(Move(tmp2,And(o1, High8)))
                    res.append(Move(bith8,RShift(bith8,Const(8))))
            elif op1 in ('bp', 'si', 'di', 'sp'):
                    bit32 = Var('e'+op1)
                    tmp = Temp()
                    SSAs.append(Move(tmp,And(bit32, High16)))
                    SSAs.append(Move(bit32,Or(V('tmp'), o1)))
            elif op1 in ('al','bl', 'cl', 'dl'):
                    bit32 = Var('e'+op1[0]+'x')
                    bit16 = Var(op1[0]+'x')
                    tmp1 = Temp()
                    tmp2 = Temp()
                    res.append(Move(tmp1, And(bit16, High8)))
                    res.append(Move(bit16, Or(tmp1, o1)))
                    res.append(Move(tmp2,And(bit32, High24)))
                    res.append(Move(bit32,Or(tmp2,o1)))
            elif op1 in ('ah','bh', 'ch', 'dh'):
                    bit32 = Var('e'+op1[0]+'x')
                    bit16 = Var(op1[0]+'x')
                    tmp1 = Temp()
                    tmp2 = Temp()
                    tmp3 = Temp()
                    res.append(Move(tmp1, And(bit16, Low8)))
                    res.append(Move(tmp2,LShift(o1, Const(8))))
                    res.append(Move(bit16,Or(tmp1, tmp2)))
                    res.append(Move(tmp3,And(bit32, High16Low8)))
                    res.append(Move(bit32,Or(tmp2, tmp3)))
            return res
        return wrapper
    return wrap
# WARNING DEFINED FOR FUNCTIONS TAKING NO ARGUMENTS!!
def assigns_ops(op=[], reg=[]):
    def wrap(f):
        for o in op:
            f = assigns_op(op=o)(f)
        for r in reg:
            f = assigns_op(reg=r)(f)
        return f
    return wrap
def resflags(op, zf=1,sf=1,pf=1):
    return [Move(Var('zf'), Func("ISZERO",[op])),
            Move(Var('sf'), Func("SIGN",[op])),
            Move(Var('pf'), Func("PARITY",[op]))]
def bitflags(op, zf=1,sf=1,pf=1):
    return resflags(op) + [Move(Var('cf'), Const(0)),
            Move(Var('of'), Const(0))]
def update_bitflags(f):
    def wrapper(*args):
        res = f(*args)
        res += bitflags(args[0])
        return res    
    return wrapper    
def update_resflags(f):
    def wrapper(*args):
        res = f(*args)
        res += resflags(args[0])
        return res    
    return wrapper    
def addflags(op1, op2, res, cf=1, of=1):
    ret = []
    if cf:
        ret.append(Move(Var('cf'), Func("ADDCARRY", [op1,op2, res])))
    if of:
        ret.append(Move(Var('of'), Func("ADDOVERFLOW", [op1,op2, res])))
    return ret
def subflags(op1, op2, res, cf=1, of=1):
    ret = []
    if cf:
        ret.append(Move(Var('cf'), Func("SUBCARRY", [op1,op2, res])))
    if of:
        ret.append(Move(Var('of'), Func("SUBOVERFLOW", [op1,op2, res])))
    return ret

@assigns_op(1)
def mov(op1, op2):
    return [Move(op1, op2)]

@assigns_op(1)
@assigns_op(2)
def xchg(op1, op2):
    tmp = Temp()
    return [Move(tmp, op1),
            Move(op1, op2),
            Move(op2, tmp)]

@assigns_op(reg=Var('esp'))    
def call(addr):
    return _push(Var('eip'))+[Jump(addr)]

@assigns_op(reg=Var('esp'))
def retn(addr=None):
    ret = _pop(Var('eip'))
    if addr:
        ret += [Move(Var('esp'),Add(Var('esp'), addr))]
    ret += [Jump(Var('eip'))]
    return ret

def jmp(addr):
    return [Jump(addr)]
def ja(addr):
    return [Branch(addr, EQ,Or(Var('zf'), Var('cf')),Const(0))]
def jae(addr):
    return [Branch(addr, EQ,Var('cf'),Const(0))]
jnb = jae
jnc = jae
def jb(addr):
    return [Branch(addr, EQ,Var('cf'),Const(1))]
jnae = jb
jc = jb
def jbe(addr):
    return [Branch(addr, EQ,Or(Var('zf'), Var('cf')),Const(1))]
jna = jbe
def jcxz(addr):
    return [Branch(addr, EQ,Var('cx'),Const(0))]
def jecxz(addr):
    return [Branch(addr, EQ,Var('ecx'),Const(0))]
def jz(addr):
    return [Branch(addr, EQ,Var('zf'),Const(1))]
je = jz
def jnz(addr):
    return [Branch(addr, EQ,Var('zf'),Const(0))]
jne = jnz
def jg(addr): # zf = 0 and sf=of
    return [Branch(addr, BOTH0,Xor(Var('sf'),Var('of')),Var('zf'))]
def jge(addr): # sf=of
    return [Branch(addr, EQ,Xor(Var('sf'),Var('of')),Const(0))]
def jl(addr): # sf<>of
    return [Branch(addr, EQ,Xor(Var('sf'),Var('of')),Const(1))]
def jle(addr): # zf = 1 and sf<>of
    return [Branch(addr, BOTH1,Xor(Var('sf'),Var('of')),Var('zf'))]
jng = jle
jnge= jl
jnl = jge
jnle= jg
def jno(addr):
    return [Branch(addr, EQ,Var('of'),Const(0))]
def jnp(addr):
    return [Branch(addr, EQ,Var('pf'),Const(0))]
def jns(addr):
    return [Branch(addr, EQ,Var('sf'),Const(0))]
def jo(addr):
    return [Branch(addr, EQ,Var('of'),Const(1))]
def jp(addr):
    return [Branch(addr, EQ,Var('pf'),Const(1))]
jpe = jp
jpo = jnp
def js(addr):
    return [Branch(addr, EQ,Var('sf'),Const(1))]


# COMPARISON/FLAGS/MISC
def nop():
    return []
def stc():
    return [Move(Var('cf'), Const(1))]
def test(op1, op2):
    tmp = Temp()
    return [Move(tmp, And(op1, op2))] + bitflags(tmp)

def cmp(op1, op2):
    tmp = Temp()
    return ([Move(tmp, Sub(op1, op2))] + 
            subflags(op1, op2, tmp) +
            resflags(tmp))
# ARITHMETIC

@assigns_op(1)
@update_resflags
def add(op1, op2):
    tmp = Temp()
    return ([Move(tmp, Add(op1, op2))] + 
            addflags(op1, op2, tmp) + 
            [Move(op1, tmp)])

@assigns_op(1)
@update_resflags
def sub(op1, op2):
    tmp = Temp()
    return ([Move(tmp, Sub(op1, op2))] + 
            subflags(op1, op2, tmp) + 
            [Move(op1, tmp)])
@assigns_op(1)
@update_resflags
def neg(op):
    tmp = Temp()
    return ([Move(tmp, Sub(Const(0), op))] + 
            subflags(Const(0), op, tmp) + 
            [Move(op, tmp)])
@assigns_op(1)
@update_resflags
def inc(op):
    tmp = Temp()
    return ([Move(tmp, Add(op, Const(1)))] + 
            addflags(op, Const(1), tmp, cf=0) + 
            [Move(op, tmp)])

@assigns_op(1)
@update_resflags
def dec(op):
    tmp = Temp()
    return ([Move(tmp, Sub(op, Const(1)))] + 
            subflags(op, Const(1), tmp, cf=0) + 
            [Move(op, tmp)])
print "HLAO"    
# BITS
@assigns_op(1)
@update_bitflags
def and_(op1, op2):
    return [Move(op1, And(op1, op2))]
@assigns_op(1)
@update_bitflags
def or_(op1, op2):
    return [Move(op1, Or(op1, op2))]
@assigns_op(1)
@update_bitflags
def xor(op1, op2):
    return [Move(op1, Xor(op1, op2))]
@assigns_op(1)
def not_(op1):
    return [Move(op1, Xor(op1, Const(0xFFFFFFFF)))]
@assigns_op(1)
@update_resflags
def shr(op, count):
    ret = []
    if count == Const(1):
        ret.append(Move(Var('of'), Func("MSB", [op])))
    ret.append(Move(Var('cf'), Func("GETBIT", [op, count])))
    ret.append(Move(op, RShift(op, count)))
    return ret
# STACK
def _push(op1):
    return [Move(Var('esp'), Sub(Var('esp'), Const(4))),
            Move(Mem(Var('esp')),op1)]
def _pop(op1):
    return [Move(op1, Mem(Var('esp'))),
            Move(Var('esp'),Add(Var('esp'),4))]

@assigns_ops(reg=[Var('ebp'), Var('esp')])
def leave():
    return _pop(Var('ebp'))

@assigns_op(reg=Var("esp"))
def push(op1):
    if isinstance(op1, Mem) and Var('esp') in op1.uses():
        tmp = Temp()
        return [Move(tmp, op1)]+_push(tmp)
    elif op1 == Var('esp'):
        tmp = Temp()
        return [Move(tmp,Var('esp'))]+_push(tmp)
    else:
        return _push(op1)

@assigns_op(1)
@assigns_op(reg=Var("esp"))
def pop(op1): #TODO Fix ESP stuff
    if isinstance(op1, Mem) and Var('esp') in op1.uses():
        tmp = Temp()
        return [Move(tmp, Mem(Var('esp'))), # Load from stack
                Move(Var('esp'),Add(Var('esp'),Const(4))), #inc
                Move(op1, tmp)] # store to memory
    elif op1 == Var('esp'):
        return [Move(Var('esp'), Mem(Var('esp')))]
    else:
        return _pop(op1)

@assigns_op(reg=Var("esp"))
def pusha():
    tmp = Temp()
    return ([Move(tmp, Var('esp'))] +
            _push(Var('eax')) +
            _push(Var('ecx')) +
            _push(Var('edx')) +
            _push(Var('ebx')) +
            _push(tmp) +
            _push(Var('ebp')) +
            _push(Var('esi')) +
            _push(Var('edi')))

@assigns_ops(reg=[Var('eax'), Var('ebx'), Var('ecx'), Var('edx'),Var('esi'), Var('edi'), Var('ebp'), Var('esp')])
def popa():
    return (_pop(Var('edi')) +
            _pop(Var('esi')) +
            _pop(Var('ebp')) +
            [Move(Var('esp'), Add(Var('esp'),4))] +
            _pop(Var('ebx')) +
            _pop(Var('edx')) +
            _pop(Var('ecx')) +
            _pop(Var('eax')))
