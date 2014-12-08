from Graph import Graph
class DominatorTree(Graph):
    # www.cs.rice.edu/~keith/EMBED/dom.pdf
    def __init__(self, root=None):
        Graph.__init__(self)
        self.entry = root
        self.build()
    def build(self):
        self.v = []
        self.e = []
        self.idom = {}
        # BUILD DOMINATOR TREE
        vertex = {}
        j = len(self.entry.graph.v)-1 # total number of vertices
        for i, v in enumerate(self.entry.dfs(pre=False)): #Reverse postorder
            vertex[j-i] = v
            v._i = i # normal postorder
            self.v.append(v)
            v._df = set()
        Changed = True
        #self.idom[self.entry] = self.entry   # root -> root
        while Changed:
            Changed = False
            for i in range(1,len(vertex)): # all except root
                b = vertex[i]
                new_idom = b.pres()[0]
                for p in filter(lambda x: x != new_idom,b.pres()):
                    if self.idom.get(p):
                        new_idom = self.intersect(p, new_idom)
                if self.idom.get(b) != new_idom:
                    self.idom[b] = new_idom
                    Changed = True
        # BUILD DOMINANCE FRONTIER SETS    
        for b in self.v:
            if len(b.pres()) >= 2:
                for p in b.pres():
                    runner = p
                    while runner != self.idom[b]:
                        runner._df.add(b)
                        runner = self.idom[runner]
        # ???
        #del self.idom[self.entry]
        # ADD EDGEES
        for v, idomv in self.idom.iteritems():
            self.add_edge(idomv,v)
    def intersect(self, b1, b2):
        finger1 = b1
        finger2 = b2
        while(finger1 != finger2):
            while(finger1._i < finger2._i):
                finger1 = self.idom[finger1]
            while(finger2._i < finger1._i):
                finger2 = self.idom[finger2]
        return finger1        
    def __str__(self):
        return "VERTICES: %s\nEDGES: %s" % (self.v, self.e)

from Graph import Vertex
def main():
    g = Graph()
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
    end = Vertex(g)
    end._id = 'end'

    g.add_edge(r, A)
    g.add_edge(r, end)

    g.add_edge(A, B)
    g.add_edge(A, C)
    g.add_edge(B, C)
    g.add_edge(C, D)
    g.add_edge(C, E)
    g.add_edge(D, F)
    g.add_edge(E, F)
    g.add_edge(F, B)
    g.add_edge(F, G)
    g.add_edge(G, end)
    dt = DominatorTree(r)
    assert (r, end) in dt.e
    assert (r, A) in dt.e
    assert (A, B) in dt.e
    assert (A, C) in dt.e
    assert (A, C) in dt.e
    assert (C, D) in dt.e
    assert (C, E) in dt.e
    assert (C, F) in dt.e
    assert (F, G) in dt.e
    g.entry = r
if __name__ == '__main__':
    main()
