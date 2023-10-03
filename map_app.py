import wx

TERRAINS = {
    "Mountain": {"value": "0", "color": wx.Colour(0, 255, 0)},
    "Land": {"value": "1", "color": wx.Colour(255, 165, 0)},
    "Water": {"value": "2", "color": wx.Colour(0, 0, 255)},
    "Sand": {"value": "3", "color": wx.Colour(255, 218, 185)},
    "Forest": {"value": "4", "color": wx.Colour(0, 128, 0)}
}

CHARACTERS = {
    "Human": {
        "Mountain": 3,
        "Land": 1,
        "Water": 2,
        "Sand": 2,
        "Forest": 2
    },
    "Sasquatch": {
        "Mountain": 1,
        "Land": 1,
        "Water": 1000,  # Sasquatch can't cross water
        "Sand": 2,
        "Forest": 1
    },
    "Monkey": {
        "Mountain": 3,
        "Land": 1,
        "Water": 3,
        "Sand": 2,
        "Forest": 1
    },
    "Octopus": {
        "Mountain": 1000,  # Octopus can't cross mountains
        "Land": 3,
        "Water": 1,
        "Sand": 2,
        "Forest": 3
    }
}

MASK_COLOR = wx.Colour(0, 0, 0)  # Black color for masking

CELL_STATES = {
    "Initial Point": "I",
    "Target": "X",
    "Visited": "V"
}

class MapApp(wx.Frame):
    def __init__(self, map_data):
        super(MapApp, self).__init__(None, title="Map Editor", size=(800, 600))
        self.map_data = map_data
        self.initUI()
        self.masked = False
        self.hasInitialPoint = False
        self.hasFinalPoint = False
        self.path = list()
        self.decision_tree = {}

    def initUI(self):
        panel = wx.Panel(self)
        grid = wx.GridSizer(len(self.map_data) + 1, len(self.map_data[0]), 10, 10)  # +1 for the finish button
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))

        self.buttons = []
        for i, row in enumerate(self.map_data):
            button_row = []
            for j, cell in enumerate(row):
                terrain, state = cell
                btn = wx.Button(panel, label=state, size=(40, 40), style=wx.BORDER_NONE)
                btn.SetBackgroundColour(self.get_terrain_color(terrain))
                btn.Bind(wx.EVT_LEFT_DOWN, lambda event, x=i, y=j: self.on_left_click(event, x, y))
                btn.Bind(wx.EVT_RIGHT_DOWN, lambda event, x=i, y=j: self.on_right_click(event, x, y))
                grid.Add(btn, 0, wx.EXPAND)
                button_row.append(btn)
            self.buttons.append(button_row)

        # Add the "Finish Editing and Start Playing" button at the bottom
        self.finish_btn = wx.Button(panel, label="Finish Editing")
        self.finish_btn.Bind(wx.EVT_BUTTON, self.on_finish_editing)
        grid.Add(self.finish_btn, 0, wx.EXPAND)
        panel.SetSizer(grid)
        self.Centre()

    def get_terrain_color(self, terrain):
        for key, attributes in TERRAINS.items():
            if attributes["value"] == terrain:
                return attributes["color"]
        return wx.Colour(255, 255, 255)  # Default white color
    
    def check_if_decision(self, i, j):
        # Check if the current cell is a decision point
        #print("A decidir:", i, ",", j)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        count_possible = 0
        for dx, dy in directions:
            x, y = i + dx, j + dy
            if 0 <= x < len(self.map_data) and 0 <= y < len(self.map_data[0]):
                terrain_value, state = self.map_data[x][y]
                terrain_name = [name for name, attributes in TERRAINS.items() if attributes["value"] == terrain_value][0]
                #print("x:",x,". y:",y," .s:", state, ". c:", CHARACTERS[self.selected_character][terrain_name], "p:", self.selected_character,". T:", terrain_name )
                if "V" not in state and "O" not in state and "I" not in state:
                    if(CHARACTERS[self.selected_character][terrain_name] < 1000):
                        count_possible += 1
        if count_possible > 1:
            return True
        else:
            return False

    def on_left_click(self, event, i, j):
        if self.masked:
        # If the clicked cell is adjacent to the current position, move there and unmask surroundings
            if abs(i - self.current_position[0]) + abs(j - self.current_position[1]) == 1 and self.map_data[i][j][1] not in ['I', 'V']:
                terrain_value, _ = self.map_data[i][j]
                terrain_name = [name for name, attributes in TERRAINS.items() if attributes["value"] == terrain_value][0]
                move_cost = CHARACTERS[self.selected_character][terrain_name]
                if move_cost < 1000:  # Ensure the character can move through the terrain
                    self.total_cost += move_cost
                    self.path.append((i, j))
                    if self.map_data[i][j][1] == 'X':
                        print("Final path taken: ", self.path)
                        dlg = wx.MessageDialog(self, f'You have reached the end of the game! Total cost: {self.total_cost}', 'Game Over', wx.OK)
                        dlg.ShowModal()
                        dlg.Destroy()
                    else:
                        if(self.check_if_decision(i,j)):
                            self.map_data[i][j] = (self.map_data[i][j][0], 'O')
                            self.buttons[i][j].SetLabel('O')
                        else:
                            self.map_data[i][j] = (self.map_data[i][j][0], 'V')
                            self.buttons[i][j].SetLabel('V')
                        self.current_position = (i, j)
                        self.unmask_surroundings(i, j)
                        self.Refresh()
        else:
            current_terrain, current_state = self.map_data[i][j]
            dlg = wx.SingleChoiceDialog(self, 'Set the cell value:', 'Edit Cell', ["Initial Point", "Target"])
            if dlg.ShowModal() == wx.ID_OK:
                new_state = CELL_STATES[dlg.GetStringSelection()]
                self.map_data[i][j] = (current_terrain, new_state)
                event.GetEventObject().SetLabel(new_state)
            dlg.Destroy()

    def on_right_click(self, event, i, j):
        dlg = wx.SingleChoiceDialog(self, 'Choose terrain type:', 'Terrain Selection', list(TERRAINS.keys()))
        if dlg.ShowModal() == wx.ID_OK:
            selected_terrain = dlg.GetStringSelection()
            self.map_data[i][j] = (TERRAINS[selected_terrain]["value"], self.map_data[i][j][1])
            event.GetEventObject().SetBackgroundColour(TERRAINS[selected_terrain]["color"])
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

    def unmask_surroundings(self, i, j):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dx, dy in directions:
            x, y = i + dx, j + dy
            if 0 <= x < len(self.map_data) and 0 <= y < len(self.map_data[0]):
                terrain, state = self.map_data[x][y]
                self.buttons[x][y].SetBackgroundColour(self.get_terrain_color(terrain))
                self.buttons[x][y].SetLabel(state)
                self.buttons[x][y].Refresh()
                self.buttons[x][y].Update()       

    def on_finish_editing(self, event):
        self.start_masking()
        self.Refresh()
        self.Update()
        dlg = wx.SingleChoiceDialog(self, 'Choose your character:', 'Character Selection', list(CHARACTERS.keys()))
        if dlg.ShowModal() == wx.ID_OK:
            self.selected_character = dlg.GetStringSelection()
            self.total_cost = 0
            self.path = []
            self.finish_btn.Disable()
        dlg.Destroy()

def read_map_from_file(filename):
    with open(filename, 'r') as file:
        return [[(char, "") for char in line.strip()] for line in file.readlines()]

if __name__ == '__main__':
    app = wx.App(False)
    map_data = read_map_from_file("map_data.txt")
    frame = MapApp(map_data)
    frame.Show()
    app.MainLoop()
