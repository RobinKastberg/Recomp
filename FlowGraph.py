from DominatorTree import DominatorTree
from Graph import Graph
from Graph import Vertex
def _flatten(lst):
	return sum( ([x] if not isinstance(x, list) else _flatten(x)
		     for x in lst), [] )
def cached_dt(f):
    def wrapper(*args):
        self = args[0]
        assert self.entry
        if self.dirty:
            if getattr(self,"dt",None):
                self.dt.entry = self.entry
                self.dt.build()
            else:
                self.dt = DominatorTree(self.entry)
            self.dirty = False
        return f(*args)
    return wrapper
class BasicBlock(Vertex):
    def merge(self, other):
        self.ir += other.ir
    def __str__(self):
        ret = ""
        ret += "\n".join(map(str, self.ir))
        return ret    
class FlowGraph(Graph):
    def __init__(self):
        Graph.__init__(self)
        self.entry = None
        self.exit = None
        self.dirty = True
    def find_by_id(self, id_):
        try:
            return filter(lambda x: x._id == id_, self.v)[0]
        except IndexError:
            return None
    @cached_dt
    def idom(self,v):
        return self.dt.pres(v)[0]
    def add_edge(self, v1, v2):
        self.dirty = True
        Graph.add_edge(self, v1, v2)
    @cached_dt
    def dominates(self, dominator, goal):
        runner = goal
        while runner != self.entry:
            runner = self.dt.idom[runner]
            if runner == dominator:
                return True
        return False
    @cached_dt
    def dominance_frontier(self,X):	
        return list(X._df)
    def dfplus(self, S):
        set_ = S
        new = set(_flatten(map(self.dominance_frontier, set_)))
        while new != set_:
            set_ = new
            new = set(_flatten(map(self.dominance_frontier, S|set_)))
        return set_
    def reduce(self):
        updated = True
        while updated:
            updated = False
            for v in self.v:
                if self.outdegree(v) == 1:
                    b = self.succs(v)[0]
                    if self.indegree(b) == 1:
                        updated = True
                        v.merge(b)
                        b_outs = self.succs(b)
                        self.delete_edge(v,b)
                        self.delete_vertex(b)
                        for out in b_outs:
                            self.delete_edge(b,out)
                            self.add_edge(v,out)
from Graph import Vertex
def main():
    g = FlowGraph()
    r = Vertex(g)
    r._id = 'root'
    A = Vertex(g)
    A._id = 'A'
    B = Vertex(g)
    B._id = 'B'
    C = Vertex(g)
    C._id = 'C'
    D = Vertex(g)
    D._id = 'D'
    E = Vertex(g)
    E._id = 'E'
    F = Vertex(g)
    F._id = 'F'
    G = Vertex(g)
    G._id = 'G'
    H = Vertex(g)
    H._id = 'H'
    end = Vertex(g)
    end._id = 'end'

    g.add_edge(r, A)
    #g.add_edge(r, end)

    g.add_edge(A, B)
    g.add_edge(A, C)
    g.add_edge(B, C)
    g.add_edge(B, D)
    g.add_edge(C, E)
    g.add_edge(D, C)
    g.add_edge(D, F)
    g.add_edge(E, B)
    g.add_edge(E, F)
    g.add_edge(F, G)
    g.add_edge(G, H)
    g.add_edge(H, A)
    g.add_edge(G, end)
    g.entry = r
    assert g.dominates(A,E)
    assert g.dominates(F,G)
    assert g.idom(end)
    print g.dt
    print g.dominance_frontier(B)
    print g.dfplus(set([E]))
if __name__ == '__main__':
    main()
