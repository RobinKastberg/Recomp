import sys
class Vertex(object):
    def __init__(self, graph):
        self.graph = graph
        self.graph.add_vertex(self)
    def __str__(self):
        return "%s(%s)" % (self.__class__, hex(self._id))
    def __repr__(self):
        return "%s(%s)" % (self.__class__, hex(self._id))
    def indegree(self, v):
        return len(self.pres())
    def outdegree(self, v):
        return len(self.succs())
    def __eq__(self, other):
        return self is other


    # Syntactic sugar
    def dfs(self,**kwargs):
        for v in self.graph.dfs(self, **kwargs):
            yield v
    def succs(self):
        return self.graph.succs(self)
    def pres(self):
        return self.graph.pres(self)
class Graph(object):
    def __init__(self):
        self.v = []
        self.e = []
    def indegree(self, v):
        return len(self.pres(v))
    def outdegree(self, v):
        return len(self.succs(v))
    def succs(self,v):
        return [e[1] for e in self.e if e[0] == v]
    def pres(self,v):
        return [e[0] for e in self.e if e[1] == v]
    def dfs(self, root=None,pre=True):
        self._dfs_visited = []
        for v in self.dfs_aux(root,pre=pre):
            yield v
    def dfs_aux(self,v=None,pre=True):
        if not v:
            v = self.entry
        if pre:    
            yield v
        for w in self.succs(v):
            if not w in self._dfs_visited:
                w._dfs_parent = v
                self._dfs_visited.append(w)
                for child in self.dfs_aux(w,pre):
                    yield child
        if not pre:
            yield v
    def add_vertex(self, v):
        if v in self.v:
            print "WARNING: Vertex already exists"
        else:
            self.v.append(v)
            return v
    def add_edge(self, v1, v2):
        if not v1 in self.v or not v2 in self.v:
            raise "No such vertex"
        if (v1, v2) in self.e:
            print "DUP!"
        self.e.append((v1, v2))
    def delete_edge(self, v1, v2):
        self.e.remove((v1, v2))
    def delete_vertex(self, v):
        self.v.remove(v)

    def update_vertex(self, vold, vnew):
        def ue(edge):
            if edge[0] == vold:
                edge = (vnew, edge[1])
            if edge[1] == vold:
                edge = (edge[0], vnew)
            return edge
        self.delete_vertex(vold)
        self.add_vertex(vnew)
        self.e = map(ue, self.e)
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
if __name__ == '__main__':
    main()
