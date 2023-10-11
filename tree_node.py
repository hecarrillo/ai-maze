class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []
        self.actions = []
        self.actionsExecuted = []
        self.other = ""

    def add_child(self, child_node):
        self.children.append(child_node)