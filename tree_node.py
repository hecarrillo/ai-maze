class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []
        self.actions = []
        self.actionsExecuted = []
        self.other = ""
        self.cost = 0
        self.total_cost = 0
        
    def __lt__(self, other):
        return self.total_cost < other.total_cost

    def add_child(self, child_node):
        self.children.append(child_node)