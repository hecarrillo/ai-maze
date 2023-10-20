from time import sleep
import wx
import networkx as nx
import matplotlib.pyplot as plt
import heapq
from networkx.drawing.nx_pydot import graphviz_layout

from constants import TERRAINS, DIRECTIONS, DIRECTION_OF_LETTER, CHARACTERS, MASK_COLOR, CELL_STATES, OBJECTIVES, ROUTES
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
        self.initialPoint = (-1, -1)
        self.finalPoint = (-1, -1)
        self.initialHuman = (-1, -1)
        self.initialOctopus = (-1, -1)
        self.portalKey = (-1, -1)
        self.darkTemple = (-1, -1)
        self.portal = (-1, -1)
        self.routes = []
        self.route_costs = []
        self.path_costs = []
        self.path = []
        self.assignation = []


    
    """UI INITIALIZATION"""
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
        self.finish_btn = wx.Button(panel, label="Solve")
        self.finish_btn.Bind(wx.EVT_BUTTON, self.solve_game)
        grid.Add(self.finish_btn, 0, wx.EXPAND)

        panel.SetSizer(grid)
        self.Centre()

    
    """GENERIC UTILS"""
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

    """USER ACTIONS HANDLERS"""
    def on_left_click(self, event, i, j):
        if self.masked:
            self.handle_masked_click(i, j)
        else:
            self.handle_unmasked_click(i, j, event)
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
    def solve_game(self, _):
        self.Refresh()
        self.Update()
        self.DIRECTIONS = DIRECTIONS
        self.solve_a_star()
        #self.highlight_path()
        
    """USER ACTIONS UTILS"""
    def handle_unmasked_click(self, i, j, event):
        current_terrain, current_state = self.map_data[i][j]
        dlg = wx.SingleChoiceDialog(self, 'Set the cell value:', 'Edit Cell', [
                                    "Human", "Octopus", "Portal Key", "Dark Temple", "Portal"])
        if dlg.ShowModal() == wx.ID_OK:
            new_state = CELL_STATES[dlg.GetStringSelection()]
            if new_state == "H":
                if self.is_valid_cell(self.initialHuman[0], self.initialHuman[1]):
                    self.map_data[self.initialHuman[0]][self.initialHuman[1]] = (self.map_data[self.initialHuman[0]][self.initialHuman[1]][0], "")
                    self.buttons[self.initialHuman[0]][self.initialHuman[1]].SetLabel("")
                self.initialHuman = (i, j)
            elif new_state == "O":
                if self.is_valid_cell(self.initialOctopus[0], self.initialOctopus[1]):
                    self.map_data[self.initialOctopus[0]][self.initialOctopus[1]] = (self.map_data[self.initialOctopus[0]][self.initialHuman[1]][0], "")
                    self.buttons[self.initialOctopus[0]][self.initialOctopus[1]].SetLabel("")
                self.initialOctopus = (i, j)
            elif new_state == "K":
                if self.is_valid_cell(self.portalKey[0], self.portalKey[1]):
                    self.map_data[self.portalKey[0]][self.portalKey[1]] = (self.map_data[self.portalKey[0]][self.initialHuman[1]][0], "")
                    self.buttons[self.portalKey[0]][self.portalKey[1]].SetLabel("")
                self.portalKey = (i, j)
            elif new_state == "D":
                if self.is_valid_cell(self.darkTemple[0], self.darkTemple[1]):
                    self.map_data[self.darkTemple[0]][self.darkTemple[1]] = (self.map_data[self.darkTemple[0]][self.initialHuman[1]][0], "")
                    self.buttons[self.darkTemple[0]][self.darkTemple[1]].SetLabel("")
                self.darkTemple = (i, j)
            elif new_state == "P":
                if self.is_valid_cell(self.portal[0], self.portal[1]):
                    self.map_data[self.portal[0]][self.portal[1]] = (self.map_data[self.portal[0]][self.initialHuman[1]][0], "")
                    self.buttons[self.portal[0]][self.portal[1]].SetLabel("")
                self.portal = (i, j)
                
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

    """MAP VALUES UTILS"""
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
    def is_valid_cell(self, i, j):
        return 0 <= i < len(self.map_data) and 0 <= j < len(self.map_data[0])
    def get_terrain_color(self, terrain):
        for _, attributes in TERRAINS.items():
            if attributes["value"] == terrain:
                return attributes["color"]
        return wx.Colour(255, 255, 255)  # Default white color
    
    """SEARCH ALGORITHMS INITIALIZATION"""
    def init_search_root(self, start):
        self.visited = set()
        print('initial position:', start)
        self.root = TreeNode((start[0], start[1], 'I'))
        self.root.other = "Initial Point"
    def solve_a_star(self):
        self.do_possible_routes(0)
        start = (-1,-1)
        end = (-1, -1)
        routes_human = []
        for route in self.routes:
            if route[0] == 'I':
                start = self.initialHuman
            elif route[0] == 'D':
                start = self.darkTemple
            elif route[0] == 'K':
                start = self.portalKey
            elif route[0] == 'P':
                start = self.portal
            if route[1] == 'I':
                end = self.initialHuman
            elif route[1] == 'D':
                end = self.darkTemple
            elif route[1] == 'K':
                end = self.portalKey
            elif route[1] == 'P':
                end = self.portal
            self.clear_visited_cells()
            self.init_search_root(start)
            self.finalPoint = end
            cost = self.a_star(start, end, "Human")
            routes_human.append((route,cost))
            self.append_actions_to_nodes(self.root) 
        routes_octopus = []
        for route in self.routes:
            if route[0] == 'I':
                start = self.initialOctopus
            elif route[0] == 'D':
                start = self.darkTemple
            elif route[0] == 'K':
                start = self.portalKey
            elif route[0] == 'P':
                start = self.portal
            if route[1] == 'I':
                end = self.initialOctopus
            elif route[1] == 'D':
                end = self.darkTemple
            elif route[1] == 'K':
                end = self.portalKey
            elif route[1] == 'P':
                end = self.portal
            self.clear_visited_cells()
            self.init_search_root(start)
            self.finalPoint = end
            cost = self.a_star(start, end, "Octopus")
            routes_octopus.append((route,cost))
            self.append_actions_to_nodes(self.root)
        self.route_costs.append(routes_human)
        self.route_costs.append(routes_octopus) 
        self.print_routes()
        self.calc_path_costs()
        self.print_path_costs()
        self.assignation = self.calc_best_assignation()
        self.print_assignation()
        self.highlight_path()
        
    def give_position(self, character, letter):
        position = (-1,-1)
        if letter == 'I':
            if character == "Human":
                position = self.initialHuman
            else:
                position = self.initialOctopus
        elif letter == 'D':
            position = self.darkTemple
        elif letter == 'K':
            position = self.portalKey
        elif letter == 'P':
            position = self.portal
        return position

    """SEARCH ALGORITHM VISUALIZATION UTILS"""
    def highlight_path(self):
        human_path = self.assignation[0][0][0]
        octopus_path = self.assignation[0][1][0]
        for i in range(len(human_path)-1):
            start = self.give_position("Human", human_path[i])
            end = self.give_position("Human", human_path[i+1])
            self.clear_visited_cells()
            self.init_search_root(start)
            self.finalPoint = end
            cost = self.a_star(start, end, "Human")
            if cost != -1:
                self.paint_path("Human", i)
        for i in range(len(octopus_path)-1):
            start = self.give_position("Octopus", octopus_path[i])
            end = self.give_position("Octopus", octopus_path[i+1])
            self.clear_visited_cells()
            self.init_search_root(start)
            self.finalPoint = end
            cost = self.a_star(start, end, "Octopus")
            if cost != -1:
                self.paint_path("Octopus", i)
    def paint_path(self, character, iteration):
        queue = []
        def traverse_tree(node):
            if node.other == "Closed Path":
                # change cell background color to red
                if character == "Human":
                    queue.append((node.value[0], node.value[1], wx.Colour((100+(50*iteration)), 0, 0)))
                else:
                    queue.append((node.value[0], node.value[1], wx.Colour(50+(50*iteration), 50+(50*iteration), 0)))
                return True
            else:
                for child in node.children:
                    if traverse_tree(child):
                        # change cell background color to red
                        if character == "Human":
                            queue.append((node.value[0], node.value[1], wx.Colour((100+(50*iteration)), 0, 0)))
                        else:
                            queue.append((node.value[0], node.value[1], wx.Colour(50+(50*iteration), 50+(50*iteration), 0)))                            
                        return True
                return False
        def paint():
            queue.reverse()
            for cell in queue:
                self.buttons[cell[0]][cell[1]].SetBackgroundColour(cell[2])
                self.buttons[cell[0]][cell[1]].Refresh()
                self.Update()
                sleep(0.4)
        traverse_tree(self.root)
        paint()

    
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

    
    """SEARCH ALGORITHMS UTILS"""
    def print_assignation(self):
        print("\nBest Assignation:")
        print(f"\tHuman: path {self.assignation[0][0][0]}. cost: {self.assignation[0][0][1]}")
        print(f"\tOctopus: path {self.assignation[0][1][0]}. cost: {self.assignation[0][1][1]}")
        print(f"\tTotal cost: {self.assignation[1]}")
    def calc_best_assignation(self):
        min_assignation = (None, 1000000)
        for human_path in self.path_costs[0]:
            for octopus_path in self.path_costs[1]:
                if(human_path[1] == -1 or octopus_path[1] == -1):
                    continue
                total_cost = human_path[1] + octopus_path[1]
                if total_cost < min_assignation[1]:
                    completed = []
                    for i in range(len(human_path[0])):
                        if human_path[0][i] not in completed:
                            completed.append(human_path[0][i])
                    for i in range(len(octopus_path[0])):
                        if octopus_path[0][i] not in completed:
                            completed.append(octopus_path[0][i])
                
                    visited_all = True
                    for point in "IKDP":
                        if point not in completed:
                            visited_all = False
                            break
                    if visited_all == True:
                        min_assignation = ((human_path, octopus_path), total_cost)
        return min_assignation
                
    def print_path_costs(self):
        print("\nHuman:")
        for path in self.path_costs[0]:
            print(f"\t{path[0]}: {path[1]}")
        print("Octopus:")
        for path in self.path_costs[1]:
            print(f"\t{path[0]}: {path[1]}")
    def calc_path_costs(self):
        self.path_costs = [[],[]]
        for c in range(2):
            for path in ROUTES:
                cost = 0
                start = path[0]
                for i in range(1, len(path)):
                    end = path[i]
                    for route in self.route_costs[c]:
                        if route[0][0] == start and route[0][1] == end:
                            if(route[1] == -1):
                                cost = -1
                                start = end
                                break
                            cost += route[1]
                            start = end
                            break
                    if cost == -1:
                        break
                   
                self.path_costs[c].append((path,cost))
    def print_routes(self):
        print("")
        print("\t", end="")
        for rout in self.routes:
            print(f"{rout[0]}->{rout[1]}\t", end="")
        print("")
        char_name = 1
        for character in self.route_costs:
            if char_name == 1:
                print(f"H:", end='\t')
                char_name = 2
            else:
                print(f"O:", end='\t')
            for rout in character:
                print(f"{rout[1]}", end="\t")
            print("")
    def clear_visited_cells(self):
        for i, row in enumerate(self.map_data):
            for j, cell in enumerate(row):
                terrain, state = cell
                if state == 'V' or state == 'C':
                    self.map_data[i][j] = (terrain, '')
                    self.buttons[i][j].SetLabel('')
    def manhattan_distance_to_end(self, node):
        return (abs(node.value[0] - self.finalPoint[0]) + abs(node.value[1] - self.finalPoint[1]))
    def label_current_cell_as_visited(self, i, j, node):
        if self.get_cell_value(i, j) in "HODKP":
            self.map_data[i][j] = (self.map_data[i][j][0], f"{self.get_cell_value(i, j)}({node.total_cost})")
        elif len(node.actions) > 1:
            self.map_data[i][j] = (self.map_data[i][j][0], f"C({node.total_cost})")
        else:
            self.map_data[i][j] = (self.map_data[i][j][0], f"V({node.total_cost})")
    def direction_taken(self, i, j, parent_node):
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
    def append_actions_to_nodes(self, node):
        if node is None:
            return
        for child in node.children:
            if child is not None and self.map_data[child.value[0]][child.value[1]][1] == 'V' or self.map_data[child.value[0]][child.value[1]][1] == 'O':
                node.actionsExecuted.append(child.value[2])
            self.append_actions_to_nodes(child)
    
    """ SEARCH ALGORITHMS IMPLEMENTATIONS """
    def do_possible_routes(self, start):
        used = set()
        for i in range(len(OBJECTIVES)-1):
            for j in range(1,len(OBJECTIVES)):
                if i != j and (i,j) not in used:
                    self.routes.append((OBJECTIVES[i], OBJECTIVES[j], -1))
                    print(f"start: {OBJECTIVES[i]}, end: {OBJECTIVES[j]}")
                    used.add((i,j))

        #for i in range(start+1, len(OBJECTIVES)):
        #    self.routes.append((OBJECTIVES[start], OBJECTIVES[i], -1))
        #    print(f"start: {OBJECTIVES[start]}, end: {OBJECTIVES[i]}")
        #    self.do_possible_routes(i)

    def a_star(self, start, end, character):
        self.selected_character = character
        self.current_position = start
        self.root.total_cost = self.manhattan_distance_to_end(self.root)
        queue = [(self.root.total_cost, self.root)]
        heapq.heapify(queue)
        while queue:
            current_node = heapq.heappop(queue)[1]
            x, y = current_node.value[:2]
            self.visited.add((x, y))

            if current_node.value[:2] == end:
                current_node.other = "Closed Path"
                self.label_current_cell_as_visited(x, y, current_node)
                return current_node.cost

            for dx, dy in self.DIRECTIONS:
                new_x, new_y = x + dx, y + dy
                if self.is_valid_cell(new_x, new_y) and (new_x, new_y) not in self.visited and self.get_cell_cost(new_x, new_y) < 1000:
                    action = self.possible_move(x, y, new_x, new_y)
                    current_node.actions.append(action)
                    node = TreeNode((new_x, new_y, self.direction_taken(new_x, new_y, current_node)))
                    node.cost = current_node.cost + self.get_cell_cost(new_x, new_y)
                    node.total_cost = node.cost + self.manhattan_distance_to_end(node)
                    heapq.heappush(queue, (node.total_cost, node))
                    current_node.add_child(node)
                    #self.visited.add((new_x, new_y))

            self.label_current_cell_as_visited(x, y, current_node)
        return -1

if __name__ == '__main__':
    app = wx.App(False)
    map_data = read_map_from_file("map_data_proyecto.txt")
    frame = MapApp(map_data)
    frame.Show()
    app.MainLoop()
