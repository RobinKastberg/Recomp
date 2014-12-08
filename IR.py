# Main class
class Tree(object):
    def __init__(self, children=[]):
        self.children = children
    def walk(self):
        yield self
        for child1 in self.children:
            for child in child1.walk():
                yield child
    def uses(self):
        return [s for s in self.walk() if type(s) in (Var, Temp, Mem)]
    def assigns(self):
        return [s.children[0] for s in self.walk() if type(s) is Move]
# Statements            
class Stmt(Tree):
	def __eq__(self, other):
		return type(self) == type(other) and  \
		self.children == other.children
EQ = 0
BOTH0 = 1
BOTH1 = 2
class Label(Stmt):
    def __init__(self, name):
        Tree.__init__(self,[])
        self.name = name
    def __str__(self):    
        return "Label(%s)" % self.name
    def __repr__(self):    
        return "Label(%s)" % self.name
class Branch(Stmt):
    def __init__(self, addr, pred, v1, v2):
        Tree.__init__(self,[v1, v2])
class Jump(Stmt):
	def __init__(self, v1):
		Tree.__init__(self,[v1])
                self.target = v1
        def __str__(self):
            return "Jump(%s)" % str(self.target)
class Move(Stmt):
	def __init__(self, lhs, rhs):
		Tree.__init__(self,[lhs, rhs])
		self.lhs = lhs
		self.rhs = rhs
        def __str__(self):
            return "%s = %s" % (str(self.lhs), str(self.rhs))
class Exit(Stmt):
	pass
# Expressions
class Expr(Tree):
	def __eq__(self, other):
		return type(self) == type(other) and  \
		self.children == other.children and \
		self.value == other.value
        def __str__(self):
            return "%s(%s)" % (self.text, ",".join(map(str, self.children)))
class Mem(Expr):
	def __init__(self, addr,bits=32):
		Tree.__init__(self, [addr])
		self.value = "mem"
                self.bits = bits
                self.text = "Mem%d" % self.bits
class Const(Expr):
	def __init__(self, value, bits=32):
		Tree.__init__(self, [])
		self.value = value
                self.bits = bits
        def __str__(self):
            return "Const%d(0x%X)" % (self.bits, self.value)
        def __repr__(self):
            return "Const%d(0x%X)" % (self.bits, self.value)
class Var(Expr):
	def __init__(self, name, bits=32,i=0):
		Tree.__init__(self, [])
		self.name = name
		self.value = (name,i)
                self.bits = bits
                self.text = "Var"
        def __repr__(self):
            return "Var(%s)" % self.name
        def __str__(self):
            return "Var(%s)" % self.name
class Temp(Expr):
	i = 0
	def __init__(self, i=None):
		Tree.__init__(self, [])
		if i:
			self.value = i
		else:
			self.value = Temp.i
			Temp.i += 1
        def __str__(self):
            return "Temp(%d)" % self.value
# Functions        
class Func(Expr):
	def __init__(self, func, args):
		Tree.__init__(self, args)
		self.value = func
                self.text = func
# Arithmetic                
class Mul(Func):
    def __init__(self, left, right):
        Func.__init__(self, "Mul", [left, right])
class Add(Func):
    def __init__(self, left, right):
        Func.__init__(self, "Add", [left, right])
class Sub(Func):
    def __init__(self, left, right):
        Func.__init__(self, "Sub", [left, right])

# Bit
class And(Func):
    def __init__(self, left, right):
        Func.__init__(self, "And", [left, right])
class Or(Func):
    def __init__(self, left, right):
        Func.__init__(self, "Or", [left, right])
class Xor(Func):
    def __init__(self, left, right):
        Func.__init__(self, "Xor", [left, right])
class Not(Func):
    def __init__(self, op):
        Func.__init__(self, "Not", [op])
class LShift(Func):
    def __init__(self, left, right):
        Func.__init__(self, "Lshift", [left, right])
class RShift(Func):
    def __init__(self, left, right):
        Func.__init__(self, "Rshift", [left, right])
