########################################################################
# amara/xpath/compiler/__init__.py
"""
A flow graph representation for Python bytecode.
"""
import dis
import new
import array
import itertools
from compiler.consts import CO_OPTIMIZED, CO_NEWLOCALS

class assembler:
    """A flow graph representation for Python bytecode as a function body"""

    postorder = None

    def __init__(self):
        self.entry = self.current = basicblock(0)
        self.blocks = [self.entry]

    def new_block(self):
        block = basicblock(len(self.blocks))
        self.blocks.append(block)
        return block

    def next_block(self, block=None):
        if block is None:
            block = basicblock(len(self.blocks))
            self.blocks.append(block)
        self.current.next = block
        self.current = block
        return block

    def emit(self, *instructions):
        hasarg = self.hasarg
        hasjump = self.hasjump
        add = self.current.append

        instructions = iter(instructions)
        for opname in instructions:
            instr = instruction(opname)
            if opname in hasarg:
                oparg = instructions.next()
                if opname in hasjump:
                    assert isinstance(oparg, basicblock)
                    instr.target = oparg
                else:
                    instr.oparg = oparg
                instr.hasarg = True
            add(instr)
        return

    # -- PyFlowGraph --------------------------------------------------

    def assemble(self, name, args, docstring, filename, firstlineno):
        """Get a Python code object"""
        self.next_block()
        self.emit('RETURN_VALUE')
        stacksize = self._compute_stack_size()
        blocks = self._get_blocks_in_order()
        consts, names, varnames = \
            self._compute_lookups(blocks, args, docstring)
        bytecode = self._compute_jump_offsets(blocks)
        codestring = bytecode.tostring()
        return new.code(len(args), len(varnames), stacksize,
                        CO_OPTIMIZED | CO_NEWLOCALS, codestring,
                        consts, names, varnames, filename, name,
                        firstlineno, '', (), ())

    def _compute_stack_size(self):
        """Return the blocks in reverse dfs postorder"""
        stack_effect = {
            'POP_TOP': -1,
            'ROT_TWO': 0,
            'ROT_THREE': 0,
            'DUP_TOP': 1,
            'ROT_FOUR': 0,

            'UNARY_POSITIVE': 0,
            'UNARY_NEGATIVE': 0,
            'UNARY_NOT': 0,
            'UNARY_CONVERT': 0,
            'UNARY_INVERT': 0,

            'LIST_APPEND': -2,

            'BINARY_POWER': -1,
            'BINARY_MULTIPLY': -1,
            'BINARY_DIVIDE': -1,
            'BINARY_MODULO': -1,
            'BINARY_ADD': -1,
            'BINARY_SUBTRACT': -1,
            'BINARY_SUBSCR': -1,
            'BINARY_FLOOR_DIVIDE': -1,
            'BINARY_TRUE_DIVIDE': -1,
            'INPLACE_FLOOR_DIVIDE': -1,
            'INPLACE_TRUE_DIVIDE': -1,

            'SLICE+0': 1,
            'SLICE+1': 0,
            'SLICE+2': 0,
            'SLICE+3': -1,

            'STORE_SLICE+0': -2,
            'STORE_SLICE+1': -3,
            'STORE_SLICE+2': -3,
            'STORE_SLICE+3': -4,

            'DELETE_SLICE+0': -1,
            'DELETE_SLICE+1': -2,
            'DELETE_SLICE+2': -2,
            'DELETE_SLICE+3': -3,

            'INPLACE_ADD': -1,
            'INPLACE_SUBSTRACT': -1,
            'INPLACE_MULTIPLY': -1,
            'INPLACE_DIVIDE': -1,
            'INPLACE_MODULO': -1,
            'STORE_SUBSCR': -3,
            'DELETE_SUBSCR': -2,

            'BINARY_LSHIFT': -1,
            'BINARY_RSHIFT': -1,
            'BINARY_AND': -1,
            'BINARY_XOR': -1,
            'BINARY_OR': -1,
            'INPLACE_POWER': -1,
            'GET_ITER': 0,

            'PRINT_EXPR': -1,
            'PRINT_ITEM': -1,
            'PRINT_NEWLINE': 0,
            'PRINT_ITEM_TO': -2,
            'PRINT_NEWLINE_TO': -1,

            'INPLACE_LSHIFT': -1,
            'INPLACE_RSHIFT': -1,
            'INPLACE_AND': -1,
            'INPLACE_XOR': -1,
            'INPLACE_OR': -1,

            'BREAK_LOOP': 0,
            'RETURN_VALUE': -1,
            'YIELD_VALUE': 0,

            'STORE_NAME': -1,
            'DELETE_NAME': 0,
            'FOR_ITER': 1,

            'STORE_ATTR': -2,
            'DELETE_ATTR': -1,
            'STORE_GLOBAL': -1,
            'DELETE_GLOBAL': 0,
            'LOAD_CONST': 1,
            'LOAD_NAME': 1,
            'BUILD_MAP': 1,
            'LOAD_ATTR': 0,
            'COMPARE_OP': -1,

            'JUMP_FORWARD': 0,
            'JUMP_IF_FALSE': 0,
            'JUMP_IF_TRUE': 0,
            'JUMP_ABSOLUTE': 0,

            'LOAD_GLOBAL': 1,

            'LOAD_FAST': 1,
            'STORE_FAST': -1,
            'DELETE_FAST': 0,
        }
        def walk(block, size, maxsize):
            block.seen = True
            instructions = iter(block)
            for instr in instructions:
                if instr in stack_effect:
                    size += stack_effect[instr]
                elif instr == 'CALL_FUNCTION':
                    size += -((instr.oparg % 256) + (2 * (instr.oparg / 256)))
                elif instr in ('BUILD_TUPLE', 'BUILD_LIST'):
                    size += (1 - instr.oparg)
                elif instr == 'UNPACK_SEQUENCE':
                    size += (instr.oparg - 1)
                elif instr == 'DUP_TOPX':
                    size += instr.oparg
                else:
                    raise RuntimeError("unhandled instruction: %r" % instr)
                if size > maxsize:
                    maxsize = size
                if instr.target is not None and not instr.target.seen:
                    assert instr in self.hasjump, instr
                    maxsize = walk(instr.target, size, maxsize)
                    if instr in ('JUMP_ABSOLUTE', 'JUMP_FORWARD'):
                        # remaining code is dead
                        break
            else:
                if block.next is not None and not block.next.seen:
                    maxsize = walk(block.next, size, maxsize)
            block.seen = False
            return maxsize

        return walk(self.entry, 0, 0)

    def _get_blocks_in_order(self):
        """Return the blocks in reverse dfs postorder"""
        def walk(block, postorder):
            """Depth-first search of tree rooted at `block`"""
            block.seen = True
            if block.next is not None and not block.next.seen:
                walk(block.next, postorder)
            for instr in block:
                if instr.target is not None and not instr.target.seen:
                    assert instr in self.hasjump, instr
                    walk(instr.target, postorder)
            postorder.append(block)
            return postorder
        return tuple(reversed(walk(self.entry, [])))

    def _compute_lookups(self, blocks, args, docstring):
        """Convert lookup arguments from symbolic to concrete form"""
        haslookup = self.haslookup
        hascompare = self.hascompare
        hasconst = self.hasconst
        haslocal = self.haslocal
        hasname = self.hasname
        cmpop = self.cmpop

        consts = {(docstring, type(docstring)): 0}
        names = {}
        varnames = {}
        for i, arg in enumerate(args):
            varnames[arg] = i

        for block in blocks:
            for instr in block:
                if instr in haslookup:
                    if instr in hasconst:
                        key = (instr.oparg, type(instr.oparg))
                        try:
                            oparg = consts[key]
                        except KeyError:
                            oparg = len(consts)
                            consts[key] = oparg
                    elif instr in haslocal:
                        try:
                            oparg = varnames[instr.oparg]
                        except KeyError:
                            oparg = len(varnames)
                            varnames[instr.oparg] = oparg
                    elif instr in hasname:
                        try:
                            oparg = names[instr.oparg]
                        except KeyError:
                            oparg = len(names)
                            names[instr.oparg] = oparg
                    elif instr in hascompare:
                        oparg = cmpop[instr.oparg]
                    else:
                        raise RuntimeError("unhandled instruction: %r" % instr)
                    instr.oparg = oparg

        if consts:
            L = ['']*len(consts)
            for key, pos in consts.iteritems():
                L[pos] = key[0]
            consts = tuple(L)
        else:
            consts = ()
        if names:
            L = ['']*len(names)
            for name, pos in names.iteritems():
                L[pos] = name
            names = tuple(L)
        else:
            names = ()
        if varnames:
            L = ['']*len(varnames)
            for name, pos in varnames.iteritems():
                L[pos] = name
            varnames = tuple(L)
        else:
            varnames = ()

        return consts, names, varnames

    def _compute_jump_offsets(self, blocks):
        """Compute the size of each block and fixup jump args"""
        hasjump = self.hasjump
        hasjrel = self.hasjrel
        hasjabs = self.hasjabs
        map = itertools.imap
        opmap = dis.opmap

        bytecode = array.array('B')
        append = bytecode.append
        extend = bytecode.extend
        while not bytecode:
            # Compute the size of each block
            offset = 0
            for block in blocks:
                block.offset = offset
                offset += sum(map(len, block))

            for block in blocks:
                for i, instr in enumerate(block):
                    if instr.target is not None:
                        assert instr in hasjump
                        if instr in hasjrel:
                            offset = len(bytecode) + len(instr)
                            instr.oparg = instr.target.offset - offset
                        elif instr in hasjabs:
                            instr.oparg = instr.target.offset
                        else:
                            raise RuntimeError("unhandled instruction: %r" %
                                               instr)
                    opcode = opmap[instr]
                    if instr.hasarg:
                        oparg = instr.oparg
                        if oparg > 0xFFFF:
                            instr.oparg &= 0xFFFF
                            instr = Instruction('EXTENDED_ARG')
                            instr.oparg = oparg >> 16
                            instr.hasarg = True
                            block.insert(i, instr)
                            break
                        extend((opcode, oparg & 0xFF, oparg >> 8))
                    else:
                        append(opcode)
                else:
                    # process the next block of instructions
                    continue
                # add an EXTENDED_ARG instruction
                assert instr == 'EXTENDED_ARG', instr
                # restart while loop to recompute offsets
                del bytecode[:]
                break
        return bytecode

    hasarg = set(dis.opname[dis.HAVE_ARGUMENT:])
    hasjrel = set(dis.opname[op] for op in dis.hasjrel)
    hasjabs = set(dis.opname[op] for op in dis.hasjabs)
    hasjump = hasjrel | hasjabs

    hascompare = set(dis.opname[op] for op in dis.hascompare)
    hasconst = set(dis.opname[op] for op in dis.hasconst)
    haslocal = set(dis.opname[op] for op in dis.haslocal)
    hasname = set(dis.opname[op] for op in dis.hasname)
    haslookup = hascompare | hasconst | haslocal | hasname

    cmpop = dict(itertools.izip(dis.cmp_op, itertools.count()))



class instruction(str):
    opname = property(str.__str__)
    oparg = None
    target = None
    hasarg = False

    def __len__(self):
        if self.hasarg:
            if self.oparg > 0xFFFF:
                return 6
            return 3
        return 1

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return '<instr at 0x%x: opname=%r, oparg=%r, target=%r>' % (
            ptr, self.opname, self.oparg, self.target)

    def __str__(self):
        return '<instr %s, oparg=%r>' % (self.opname, self.oparg)


class basicblock(list):

    __slots__ = ('id', 'label', 'next', 'seen', 'offset')

    def __init__(self, id, label=None):
        self.id = id
        self.label = label
        self.next = None
        self.seen = False
        self.offset = 0

    emit = list.append

    __hash__ = object.__hash__

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        if self.label:
            label = ', label=%s' % self.label
        else:
            label = ''
        return "<block at 0x%x: id=%d%s>" % (ptr, self.id, label)

    def __str__(self):
        if self.label:
            label = ' %r ' % self.label
        else:
            label = ''
        if self:
            instructions = ':\n  ' + '\n  '.join(map(str, self))
        else:
            instructions = ''
        return "<block %s%d, offset %d%s>" % (label, self.id, self.offset,
                                              instructions)
