def sgn32(i):
	return (i & 0x80000000) >> 31
class Disassembler(object):
	def __init__(self, start):
		self.start = start
		self.regs = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
	def _decode_instr(self,eip):
		MakeCode(eip)
		mnem = GetMnem(eip)
		x = [ItemSize(eip), mnem]
		ins = DecodeInstruction(eip)
		for i in range(2):
			ty = GetOpType(eip,i)
			if 5 <= ty <= 7:
				x.append(GetOperandValue(eip, i))
			elif ty == idc.o_displ:
				off = GetOperandValue(eip,i)
				reg = ins.Operands[i].reg
				x.append([self.regs[reg],off])
			elif ty == idc.o_phrase:
				off = GetOperandValue(eip,i)
				reg1 = ins.Operands[i].reg
				reg2 = ins.Operands[i].reg
				x.append([self.regs[reg1],0]) # TODO INDEX REG
			else:
				x.append(GetOpnd(eip, i))
		return x

	def get_instruction(self, eip):
		return self._decode_instr(eip)
class EFLAGS(object):
	flags = {'cf': 0, 'pf': 2, 'af': 4, 'zf': 6, 'sf': 7, 'df': 10, 'of': 11}
	def __init__(self, init):
		self.__dict__['e'] = init
	def __getitem__(self, i):
		return (self.e & (1 << i)) >> i
	def __setitem__(self, i, b):	
		if b:
			self.__dict__['e'] |= (1 << i)
		else:
			self.__dict__['e'] &= ~(1 << i)
	def __setattr__(self, var, bit):
		if var in EFLAGS.flags:
			self[EFLAGS.flags[var]] = bit
		else:
			self.__dict__['e'] = bit
	def __getattr__(self, var):
		if var in EFLAGS.flags:
			return self[EFLAGS.flags[var]]
		else:
			return self.__dict__['e']
	def update_res32(self, number, updateCarry=True):
		self.zf = (number == 0)
		self.sf = (number & 0x80000000)
		self.pf = ~((((number&0xff) * 0x0101010101010101) & 0x8040201008040201) % 0x1FF) & 1
		if updateCarry:
			self.cf = (number & 0xffffffff) != number
	def __str__(self):
		return "%08X" % self.__dict__['e']

class StateMachine:
	def __init__(self, start):
		self.start = start
		self.d = Disassembler(start)
		self.lst = []
		self.read_mem = []
		self.ctx = {
			'eax' : 0x76A80000,
			'ebx' : 0x0,
			'ecx' : 0x76AA16ED,
			'edx' : 0x00400000,
			'esi' : 0x2,
			'edi' : 0x76A800E8,
			'ebp' : 0xF6401014,
			'esp' : 0x013DFF64,
			'eip' : start,
			'ds'  : 0x2b,
			'eflags':EFLAGS(0x200)
		}
		self.orig_ctx = {
			'eax' : 0x76A80000,
			'ebx' : 0x0,
			'ecx' : 0x76AA16ED,
			'edx' : 0x00400000,
			'esi' : 0x2,
			'edi' : 0x76A800E8,
			'ebp' : 0xF6401014,
			'esp' : 0x013DFF64,
			'eip' : start,
			'ds'  : 0x2b,
			'eflags':EFLAGS(0x200)
		}
		self.mem = {0x13dff68: 0}
		self.tainted = []	
		self.eips = []
	def debug(self, str):
		print "(%08X): %s" % (self.ctx['eip'], str)
	def jcc(self, type):
		f = self.eflags()
		if type == 'ja':
			return f.zf == 0 and f.cf == 0
		elif type =='jnz':
			return f.zf == 0
		elif type == 'jz':
			return f.zf == 1
		elif type == 'js':
			return f.sf == 1
		elif type == 'jg':
			return (f.zf == 0) and (f.sf == f.of)
		elif type == 'jle':
			return (f.zf == 1) or (f.sf != f.of)
		elif type == 'jl':
			return (f.sf != f.of)
		elif type == 'jnp':
			return (f.pf == 0)
		elif type == 'jp':
			return (f.pf == 1)
		elif type == 'jb':
			return (f.cf == 1)
		elif type == 'jnb':
			return (f.cf == 0)
		elif type == 'jbe':
			return (f.cf == 1) or (f.zf == 1)
		elif type == 'jo':
			return (f.of == 1)	
		elif type == 'jmp':
			return True	
		else: 
			return None
	def reg_write(self, reg, value):
		if type(reg) is list: # reg+offset
			mem = (self.rim(reg[0])+self.rim(reg[1])) & 0xffffffff
			self.mem[mem] = value
			if(abs(mem - self.orig_ctx['esp']) > 0x1000):
				self.debug("MEM[%08X] = %08x" % (mem, value))
				self.tainted.append(mem)
		elif type(reg) in (int, long):
			self.mem[reg] = value
			if(abs(reg - self.orig_ctx['esp']) > 0x1000):
				self.debug("MEM[%08X] = %08x" % (mem, value))
				self.tainted.append(reg)
		elif reg in self.ctx:
			self.ctx[reg] = value & 0xffffffff
			self.tainted.append(reg)
		elif ('e'+reg) in self.ctx:
			dw = self.ctx['e'+reg]
			self.ctx['e'+reg] = (dw & 0xffff0000) | (value & 0xffff)
			self.tainted.append(self.reg_to_32bit(reg))
		elif ('e'+reg[0]+'x') in self.ctx: #TODO esi edi ebp esp, 
			dw = self.ctx['e'+reg[0]+'x']														
			r = self.reg_to_32bit(reg)
			if reg[1] == 'l':
				self.ctx[r] = (dw & 0xffffff00) | value
			elif reg[1] == 'h':										  
				self.ctx[r] = (dw & 0xffff00ff) | (value << 8)
		 	else:												 
				raise Exception("BADreg")
			self.tainted.append(self.reg_to_32bit(reg))
		else:		
			raise Exception("BADreg")
	def reg_to_32bit(self, reg):
		if ('e'+reg) in self.ctx:
			return 'e'+reg
		elif ('e'+reg[0]+'x') in self.ctx:				  
			return 'e'+reg[0]+'x'											  
		elif reg in self.ctx:
			return reg				
		# TODO 16 bit regs etc																	  
	def rim(self, x):
		if type(x) is list:
			return self.r((self.ctx[x[0]]+x[1]) & 0xffffffff) # ADDRESS
		elif type(x) in (int, long):
			return x
		elif x == '':
			return None
		elif x in self.ctx:
			return self.ctx[x]
		elif ('e'+str(x)) in self.ctx:
			return self.ctx['e'+x]&0xffff					   
		elif ('e'+str(x)[0]+'x') in self.ctx:				  
			r = 'e'+str(x)[0]+'x'				   
			if x[1] == 'l':
				return self.ctx[r] & 0x000000ff
			elif x[1] == 'h':										  
				return (self.ctx[r] & 0x0000ff00) >> 8
		else:
			return x
	def w(self,addr, x):
		self.mem[self.rim(addr)] = self.rim(x)
	def r(self,addr):
		adr = self.rim(addr)
		try:
			return self.mem[adr]
		except KeyError:
			ida = Dword(adr)
			self.debug("READING MEMORY: %08X = %08X" % (adr, ida))
			self.mem[adr] = ida
			self.read_mem.append(adr)
			return self.mem[adr]
	def push(self, op):
		if op == 'esp':
			op = self.ctx['esp']
		if type(op) is list:
			if op[0] == 'esp':
				op[1] += 4
		self.ctx['esp'] -= 4
		self.w('esp', op)
	def pop(self, op):	
		if type(op) is list:
			if op[0] == 'esp':
				op[1] += 4 # "MODIFYING ESP FOR INDEXING"
		self.reg_write(op, self.r('esp'))
		if op != 'esp':
			self.ctx['esp'] += 4
	def pusha(self):
		tmp = self.ctx['esp']
		self.push('eax')
		self.push('ecx')
		self.push('edx')
		self.push('ebx')
		self.push(tmp)
		self.push('ebp')
		self.push('esi')
		self.push('edi')
	def popa(self):	
		self.pop('edi')
		self.pop('esi')
		self.pop('ebp')
		self.ctx['esp'] += 4
		self.pop('ebx')
		self.pop('edx')
		self.pop('ecx')
		self.pop('eax')
	def eflags(self):
		return self.ctx['eflags']
	def insns(self, times):
		i = 0
		while i < times:
			size, nm, op1, op2 = self.d.get_instruction(self.ctx['eip'])
			#print ("%08X(%d): " % (self.ctx['eip'],i)) + str([nm, op1, op2]) + (" ESI=%08X" % self.ctx['esi'])
			#if self.ctx['eip'] in self.eips:
			#	print "LOOP DETECTED"
			#else:
			#	self.eips.append(self.ctx['eip'])
			self.ctx['eip'] += size
			try:
				o1 = self.rim(op1)
			except KeyError:
				o1 = None
			try:
				o2 = self.rim(op2)
			except KeyError:
				o2 = None
			if nm == 'mov':
				self.reg_write(op1, self.rim(op2))
			elif nm == 'xchg':
				self.reg_write(op1, o2)
				self.reg_write(op2, o1)
			elif nm == 'movsx': # TODO DUMMY
				self.reg_write(op1, self.rim(op2))
			elif nm == 'lea':
				addr = (self.rim(op2[0])+self.rim(op2[1])) & 0xffffffff
				self.reg_write(op1, addr)
			elif nm == 'inc':
				res = (self.ctx[op1] + 1) & 0xffffffff
				self.reg_write(op1, res)
				self.eflags().update_res32(res, False)
				if sgn32(o1) == 0 and sgn32(res) == 1:
					self.eflags().of = 1
				else:
					self.eflags().of = 0
			elif nm == 'dec':
				res = (self.ctx[op1] - 1) & 0xffffffff
				self.reg_write(op1, res)
				self.eflags().update_res32(res, False)
				if sgn32(o1) == 1 and sgn32(res) == 0:
					self.eflags().of = 1
				else:
					self.eflags().of = 1
			elif nm == 'sub':	
				self.eflags().update_res32(o1-o2);
				if (sgn32(o1) == 0 and  sgn32(o2) == 1 and sgn32(o1-o2) == 1) or (sgn32(o1) == 1 and sgn32(o2) == 0 and sgn32(o1-o2) == 0):
					self.eflags().of = 1
				else:
					self.eflags().of = 0
				self.reg_write(op1, o1-o2)
				self.tainted.append('eflags')
			elif nm == 'add':	
				self.reg_write(op1, o1+o2)
				self.eflags().update_res32(o1+o2);
				if sgn32(o1) == sgn32(o2) and sgn32(o1+o2) != sgn32(o1):
					self.eflags().of = 1
				else:
					self.eflags().of = 0
				self.tainted.append('eflags')
			elif nm == 'neg':
				self.reg_write(op1, -o1)
				self.eflags().update_res32(-o1);
				self.eflags().of = (o1 == 0x80000000)
				self.eflags().cf = (o1 != 0)
				self.tainted.append('eflags')
			elif nm == 'not':
				self.reg_write(op1, ~o1)
			elif nm == 'and':	
				self.eflags().update_res32(o1&o2);
				self.eflags().of = 0
				self.reg_write(op1, o1&o2)
				self.tainted.append('eflags')
			elif nm == 'or':	
				self.eflags().update_res32(o1|o2);
				self.eflags().of = 0
				self.reg_write(op1, o1|o2)
				self.tainted.append('eflags')
			elif nm == 'xor':	
				self.eflags().update_res32(o1^o2);
				self.eflags().of = 0
				self.reg_write(op1, o1^o2)
				self.tainted.append('eflags')
			elif nm == 'shl': # 32bit only
				l = o1
				for s in range(0, op2):
					self.eflags().cf = (l & 0x80000000) >> 31
					l <<= 1
				if op2 == 1:
					self.eflags().of = ((l & 0x80000000) >> 31) ^ self.eflags().cf
				self.reg_write(op1, l)
				self.eflags().update_res32(l, False)
				self.tainted.append(self.reg_to_32bit(op1))
				self.tainted.append('eflags')
			elif nm == 'shr': # 32bit only
				l = self.rim(op1)
				if op2 == 1:
					self.eflags().of = ((l & 0x80000000) >> 31)
				for s in range(0, op2):
					self.eflags().cf = l & 0x1
					l >>= 1
				self.reg_write(op1, l)
				self.eflags().update_res32(l, False)
				self.tainted.append(self.reg_to_32bit(op1))
				self.tainted.append('eflags')
			elif nm == 'push':	
				self.push(op1)
			elif nm == 'pop':	
				self.pop(op1)
			elif nm == 'stc':
				self.eflags().cf = 1
			elif nm == 'test':
				res = o1 & o2
				self.eflags().cf = 0
				self.eflags().of = 0
				self.eflags().update_res32(res)
				self.tainted.append('eflags')
			elif nm == 'pusha':
				self.pusha()	
			elif nm == 'popa':
				self.popa()	
			elif nm == 'call':
				self.push(self.ctx['eip'])
				self.ctx['eip'] = op1
				print "Calling " + hex(op1)
			elif nm == 'sti':
				1
			elif self.jcc(nm) != None:
				if self.jcc(nm):
					self.ctx['eip'] = op1
					#print "Jumping to " + hex(op1)
			else:
				raise "UNHANDLED"
				self.lst.append([nm, op1, op2])
			i += 1
		self.tainted = set(self.tainted)		
		for reg in self.tainted:
			if reg in self.ctx:
				if self.ctx[reg] != self.orig_ctx[reg]:
					self.lst.insert(0,['mov', reg, self.ctx[reg]])
			else:
				self.lst.insert(0,['mov', reg, self.mem[reg]]) #mem
		self.tainted = []
		strmem = "MEM: "
		for key, value in self.mem.iteritems():
			strmem += "[%08X=%x]" % (key, value)
		print strmem
		strmem = "READ_MEM: "
		for value in self.read_mem:
			strmem += "[%08X]" % value
		print strmem
		Jump(self.ctx['eip'])
		ret = list(self.lst)
		self.lst = []
		return ret
		
def pretty(lst):
	print lst
	for inst in lst:
		if type(inst[1]) in (int,long):
			inst[1] = "0x%08X" % inst[1]
		if type(inst[2]) in (int,long):
			inst[2] = "0x%08X" % inst[2]
		inst[1] = inst[1]+","
		inst[2] = str(inst[2])
		print " ".join(inst)
d = StateMachine(0x7B29D0)
pretty(d.insns(1000))
