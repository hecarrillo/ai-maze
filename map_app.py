import wx
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout

from constants import TERRAINS, DIRECTIONS, DIRECTION_OF_LETTER, CHARACTERS, MASK_COLOR, CELL_STATES
from utils import hierarchy_pos, read_map_from_file
from tree_node import TreeNode

class MapApp(wx.Frame):
    def __init__(self, map_data):
        super(MapApp, self).__init__(None, title="Map Editor", size=(800, 600))
        self.map_data = map_data
        self.initUI()
        self.masked = False
        self.hasInitialPoint = False
        self.hasFinalPoint = False
        self.path = []

    def initUI(self):
        panel = wx.Panel(self)
        # +1 for the finish button
        grid = wx.GridSizer(len(self.map_data) + 1,
                            len(self.map_data[0]), 10, 10)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))

        self.buttons = []
        for i, row in enumerate(self.map_data):
            button_row = []
            for j, cell in enumerate(row):
                terrain, state = cell
                btn = wx.Button(panel, label=state, size=(
                    40, 40), style=wx.BORDER_NONE)
                btn.SetBackgroundColour(self.get_terrain_color(terrain))
                btn.Bind(wx.EVT_LEFT_DOWN, lambda event, x=i,
                         y=j: self.on_left_click(event, x, y))
                btn.Bind(wx.EVT_RIGHT_DOWN, lambda event, x=i,
                         y=j: self.on_right_click(event, x, y))
                grid.Add(btn, 0, wx.EXPAND)
                button_row.append(btn)
            self.buttons.append(button_row)

        # Add the "Finish Editing and Start Playing" button at the bottom
        self.finish_btn = wx.Button(panel, label="Finish Editing")
        self.finish_btn.Bind(wx.EVT_BUTTON, self.on_finish_editing)
        grid.Add(self.finish_btn, 0, wx.EXPAND)

        # Add the auto solve button that is disabled until the user finishes editing
        self.auto_solve_btn = wx.Button(panel, label="Auto Solve")
        self.auto_solve_btn.Bind(wx.EVT_BUTTON, self.auto_solve)
        grid.Add(self.auto_solve_btn, 10, wx.EXPAND)
        self.auto_solve_btn.Disable()

        panel.SetSizer(grid)
        self.Centre()

    def get_terrain_color(self, terrain):
        for key, attributes in TERRAINS.items():
            if attributes["value"] == terrain:
                return attributes["color"]
        return wx.Colour(255, 255, 255)  # Default white color

    def check_if_decision(self, i, j):
        # Check if the current cell is a decision point
        # print("A decidir:", i, ",", j)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        count_possible = 0
        for dx, dy in directions:
            x, y = i + dx, j + dy
            if 0 <= x < len(self.map_data) and 0 <= y < len(self.map_data[0]):
                terrain_value, state = self.map_data[x][y]
                terrain_name = [name for name, attributes in TERRAINS.items(
                ) if attributes["value"] == terrain_value][0]
                if CHARACTERS[self.selected_character][terrain_name] < 1000 and ("V" not in state and "O" not in state and "I" not in state):
                    count_possible += 1
        return count_possible > 1

    def plot_decision_tree(self):
        G = nx.DiGraph()

        def find_decision_maker(node):
            if len(node.actions) > 1 or node.other == "Closed Path" or len(node.actions) == 0:
                return node
            for child in node.children:
                return find_decision_maker(child)
        def traverse_tree(node):
            for child in node.children:
                next = find_decision_maker(child)
                if next is not None:
                    G.add_edge((node.value, str(node.actions), str(node.actionsExecuted), str(node.other)), (next.value, str(next.actions), str(next.actionsExecuted), str(next.other) ))
                    traverse_tree(next)

        traverse_tree(self.root)

        pos = hierarchy_pos(G, (self.root.value, str(self.root.actions), str(self.root.actionsExecuted), str(self.root.other)))
        plt.figure(figsize=(10, 10))
        labels = {node: f"Position: ({node[0][0]},{node[0][1]}), dirTaken:{node[0][2]}\nActions:{node[1]}\nActionsExecuted:{node[2]}\nOther:{node[3]}" for node in G.nodes()}
        nx.draw(G, pos=pos, with_labels=True, labels=labels, node_size=1500, node_color="skyblue", node_shape="s", alpha=0.5, linewidths=40, )
        plt.title("Decision Tree, decision by decision")
        plt.show()

    def plot_step_tree(self):
        G = nx.DiGraph()

        def traverse_tree(node):
            for child in node.children:
                G.add_edge((node.value, str(node.actions), str(node.actionsExecuted), str(node.other)), (child.value, str(child.actions), str(child.actionsExecuted), str(child.other) ))
                traverse_tree(child)

        traverse_tree(self.root)

        pos = hierarchy_pos(G, (self.root.value, str(self.root.actions), str(self.root.actionsExecuted), str(self.root.other)))
        plt.figure(figsize=(10, 10))
        labels = {node: f"Position: ({node[0][0]},{node[0][1]}), dirTaken:{node[0][2]}\nActions:{node[1]}\nActionsExecuted:{node[2]}\nOther:{node[3]}" for node in G.nodes()}
        nx.draw(G, pos=pos, with_labels=True, labels=labels, node_size=1500, node_color="skyblue", node_shape="s", alpha=0.5, linewidths=40, )
        plt.title("Decision Tree step by step")
        plt.show()

    def on_left_click(self, event, i, j):
        if self.masked:
            self.handle_masked_click(i, j)
        else:
            self.handle_unmasked_click(i, j, event)

    def handle_masked_click(self, i, j):
        if abs(i - self.current_position[0]) + abs(j - self.current_position[1]) == 1 and self.map_data[i][j][1] not in ['I', 'V']:
            terrain_value, _ = self.map_data[i][j]
            terrain_name = [name for name, attributes in TERRAINS.items(
            ) if attributes["value"] == terrain_value][0]
            move_cost = CHARACTERS[self.selected_character][terrain_name]
            if move_cost < 1000:  # Ensure the character can move through the terrain
                self.total_cost += move_cost
                self.path.append((i, j))
                if self.map_data[i][j][1] == 'X':
                    self.handle_game_over()
                else:
                    self.handle_valid_move(i, j)
                    self.current_position = (i, j)
                    self.unmask_surroundings(i, j)
                    self.Refresh()

    def handle_unmasked_click(self, i, j, event):
        current_terrain, current_state = self.map_data[i][j]
        dlg = wx.SingleChoiceDialog(self, 'Set the cell value:', 'Edit Cell', [
                                    "Initial Point", "Target"])
        if dlg.ShowModal() == wx.ID_OK:
            new_state = CELL_STATES[dlg.GetStringSelection()]
            self.map_data[i][j] = (current_terrain, new_state)
            event.GetEventObject().SetLabel(new_state)
        dlg.Destroy()

    def handle_game_over(self):
        print("Final path taken: ", self.path)
        dlg = wx.MessageDialog(
            self, f'You have reached the end of the game! Total cost: {self.total_cost}', 'Game Over', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def handle_valid_move(self, i, j):
        if self.check_if_decision(i, j):
            self.map_data[i][j] = (self.map_data[i][j][0], 'O')
            self.buttons[i][j].SetLabel('O')
        else:
            self.map_data[i][j] = (self.map_data[i][j][0], 'V')
            self.buttons[i][j].SetLabel('V')

    def on_right_click(self, event, i, j):
        dlg = wx.SingleChoiceDialog(
            self, 'Choose terrain type:', 'Terrain Selection', list(TERRAINS.keys()))
        if dlg.ShowModal() == wx.ID_OK:
            selected_terrain = dlg.GetStringSelection()
            self.map_data[i][j] = (
                TERRAINS[selected_terrain]["value"], self.map_data[i][j][1])
            event.GetEventObject().SetBackgroundColour(
                TERRAINS[selected_terrain]["color"])
            self.buttons[i][j].Refresh()
        dlg.Destroy()

    def start_masking(self):
        self.masked = True
        for i, row in enumerate(self.map_data):
            for j, cell in enumerate(row):
                terrain, state = cell
                if state != 'I':
                    self.buttons[i][j].SetBackgroundColour(MASK_COLOR)
                    self.buttons[i][j].SetLabel('')
                else:
                    self.current_position = (i, j)
                    self.path.append((i, j))
                    wx.CallLater(100, self.unmask_surroundings, i, j)

    def is_valid_cell(self, i, j):
        return 0 <= i < len(self.map_data) and 0 <= j < len(self.map_data[0])

    def unmask_surroundings(self, i, j):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dx, dy in directions:
            x, y = i + dx, j + dy
            if self.is_valid_cell(x, y):
                terrain, state = self.map_data[x][y]
                self.buttons[x][y].SetBackgroundColour(
                    self.get_terrain_color(terrain))
                self.buttons[x][y].SetLabel(state)
                self.buttons[x][y].Refresh()
                self.buttons[x][y].Update()

    def on_finish_editing(self, _):
        self.start_masking()
        self.Refresh()
        self.Update()
        dlg = wx.SingleChoiceDialog(
            self, 'Choose your character:', 'Character Selection', list(CHARACTERS.keys()))
        if dlg.ShowModal() == wx.ID_OK:
            self.selected_character = dlg.GetStringSelection()
            self.total_cost = 0
            self.path = []
            self.finish_btn.Disable()
        dlg.Destroy()

        self.auto_solve_btn.Enable()

    def auto_solve(self, _):
        # Prompt the user to select to solve either by DFS or BFS
        dlg = wx.SingleChoiceDialog(
            self, 'Choose your algorithm:', 'Algorithm Selection', ["DFS", "BFS"])
        if dlg.ShowModal() == wx.ID_OK:
            selected_algorithm = dlg.GetStringSelection()
            print(selected_algorithm)
            self.solve(selected_algorithm)
        dlg.Destroy()

    def unmask_map(self, map_data, buttons):
        for i, row in enumerate(map_data):
            for j, cell in enumerate(row):
                terrain, state = cell
                buttons[i][j].SetBackgroundColour(
                    self.get_terrain_color(terrain))
                buttons[i][j].SetLabel(state)
                buttons[i][j].Refresh()
                buttons[i][j].Update()

    def select_direction_priority(self):
        for i in range(4):
            text = 'Choose direction #' + str(i+1)
            available = []
            for op in DIRECTION_OF_LETTER.keys():
                if DIRECTION_OF_LETTER[op] not in self.DIRECTIONS:
                    available.append(op)
            dlg = wx.SingleChoiceDialog(
                self, text, 'Direction Selection', available)
            if dlg.ShowModal() == wx.ID_OK:
                selected_letter = str(dlg.GetStringSelection())
                print(selected_letter)
                self.DIRECTIONS.append(DIRECTION_OF_LETTER[selected_letter])
            dlg.Destroy()

    def select_plot_mode(self):
        dlg = wx.SingleChoiceDialog(
            self, 'Choose hot to display the decision tree:', 'tree display mode', ["Step by step", "Decision by decision"])
        if dlg.ShowModal() == wx.ID_OK:
            selected_mode = dlg.GetStringSelection()
            print(selected_mode)
            if selected_mode == "Decision by decision":
                self.plot_decision_tree()
            else:
                self.plot_step_tree()
        dlg.Destroy()        

    def solve(self, algorithm):
        # Solve the map using the selected algorithm
        self.DIRECTIONS = []
        self.select_direction_priority()
        if algorithm == "DFS":
            self.solve_dfs()
        elif algorithm == "BFS":
            self.solve_bfs()
        self.select_plot_mode()
        self.unmask_map(self.map_data, self.buttons)

    def get_terrain_name(self, i, j):
        terrain_value, _ = self.map_data[i][j]
        return [
            name
            for name, attributes in TERRAINS.items()
            if attributes["value"] == terrain_value
        ][0]

    def get_cell_cost(self, i, j):
        terrain_name = self.get_terrain_name(i, j)
        return CHARACTERS[self.selected_character][terrain_name]

    def get_cell_value(self, i, j):
        return self.map_data[i][j][1]

    def solve_dfs(self):
        self.init_search_root()
        self.dfs(self.current_position[0], self.current_position[1], None)

    def label_current_cell_as_visited(self, i, j, node):
        if self.get_cell_value(i, j) in ('I', 'X'):
            return
        if len(node.actions) > 1:
            self.map_data[i][j] = (self.map_data[i][j][0], 'O')
        else:
            self.map_data[i][j] = (self.map_data[i][j][0], 'V')

    def direction_taken(self, i, j, parent_node):
        #print('i:', i, 'j:', j, 'parent:', parent_node.value)
        #print("value:", int(parent_node.value[0]), int(parent_node.value[1]), str(parent_node.value[2]))
        if parent_node is None:
            return 'I'
        parent_i = int(parent_node.value[0])
        parent_j = int(parent_node.value[1])
        if i == parent_i and j == parent_j + 1:
            return 'R'
        elif i == parent_i + 1 and j == parent_j:
            return 'D'
        elif i == parent_i and j == parent_j - 1:
            return 'L'
        elif i == parent_i - 1 and j == parent_j:
            return 'U'
        return None
    
    def possible_move(self, i, j, x, y):
        if x == i and y == j + 1:
            return 'R'
        elif x == i + 1 and y == j:
            return 'D'
        elif x == i and y == j - 1:
            return 'L'
        elif x == i - 1 and y == j:
            return 'U'
        return None

    def dfs(self, i, j, parent_node):
        
        current_node = TreeNode((i, j, self.direction_taken(i,j,parent_node) )) if parent_node else self.root
        
        if parent_node:
            print('parent:', parent_node.value, 'current:', current_node.value)
            parent_node.add_child(current_node)
        
        if self.get_cell_value(i, j) == 'X':
            current_node.other = "Closed Path"
            return True

        self.visited.add((i, j))

        for dx, dy in self.DIRECTIONS:
            x, y = i + dx, j + dy
            if self.is_valid_cell(x, y) and (x, y) not in self.visited and self.get_cell_cost(x, y) < 1000:
                current_node.actions.append(self.possible_move(i,j,x,y))
        self.label_current_cell_as_visited(i, j, current_node)
        for dx, dy in self.DIRECTIONS:
            x, y = i + dx, j + dy
            if self.is_valid_cell(x, y) and (x, y) not in self.visited and self.get_cell_cost(x, y) < 1000:
                current_node.actionsExecuted.append(self.possible_move(i,j,x,y))
                if self.dfs(x, y, current_node):
                    return True
        return False
    
    def mark_bfs_executed(self, node):
        if node is None:
            return
        visited = 0
        for child in node.children:
            if child is not None and self.map_data[child.value[0]][child.value[1]][1] == 'V' or self.map_data[child.value[0]][child.value[1]][1] == 'O':
                node.actionsExecuted.append(child.value[2])
            self.mark_bfs_executed(child)

    def solve_bfs(self):
        self.init_search_root()
        self.bfs()
        self.mark_bfs_executed(self.root)

    # TODO Rename this here and in `solve_dfs` and `solve_bfs`
    def init_search_root(self):
        self.visited = set()
        print('initial position:', self.current_position)
        self.root = TreeNode((self.current_position[0], self.current_position[1], 'I'))
        self.root.other = "Initial Point"
    
    def bfs(self):
        queue = [self.root]
        while queue:
            current_node = queue.pop(0)
        
            self.visited.add((current_node.value[0], current_node.value[1]))
            

            if self.get_cell_value(current_node.value[0], current_node.value[1] ) == 'X':
                current_node.other = "Closed Path"
                return True
            for dx, dy in self.DIRECTIONS:
                x, y = current_node.value[0] + dx, current_node.value[1] + dy
                if self.is_valid_cell(x, y) and (x, y) not in self.visited and self.get_cell_cost(x, y) < 1000:
                    current_node.actions.append(self.possible_move(current_node.value[0], current_node.value[1],x,y))
            self.label_current_cell_as_visited(current_node.value[0], current_node.value[1], current_node)
            for dx, dy in self.DIRECTIONS:
                x, y = current_node.value[0] + dx, current_node.value[1] + dy
                if self.is_valid_cell(x, y) and (x, y) not in self.visited and self.get_cell_cost(x, y) < 1000:
                    node = TreeNode((x, y, self.direction_taken(x,y,current_node)))
                    queue.append(node)
                    current_node.add_child(node)
                    self.visited.add((x, y))

if __name__ == '__main__':
    app = wx.App(False)
    map_data = read_map_from_file("map_data.txt")
    frame = MapApp(map_data)
    frame.Show()
    app.MainLoop()
