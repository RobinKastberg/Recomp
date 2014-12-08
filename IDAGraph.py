from idaapi import GraphViewer
class IDAGraph(GraphViewer):
	def __init__(self, graph):
		GraphViewer.__init__(self, "Recomp", True)
                self.g = graph
	def OnGetText(self, node_id):
		return str(self[node_id])
	def indegree(self, v):
		return len(self.pres(v))
	def outdegree(self, v):
		return len(self.succs(v))
	def OnRefresh(self):
		self.Clear()
                ids = {}
		for v in self.g.v:
			ids[v._id] = self.AddNode(str(v))
		for v1, v2 in self.g.e:
			v1 = v1._id
			v2 = v2._id
			self.AddEdge(ids[v1],ids[v2])
		return True

	def OnCommand(self, cmd_id):
		"""
		Triggered when a menu command is selected through the menu or its hotkey
		@return: None
		"""
		if self.cmd_close == cmd_id:
			self.Close()
			return

		print "command:", cmd_id

	def Show(self):
		if not GraphViewer.Show(self):
			return False
		self.cmd_close = self.AddCommand("Close", "F2")
		if self.cmd_close == 0:
			print "Failed to add popup menu item!"
		return True
