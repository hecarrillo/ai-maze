import wx

TERRAINS = {
    "Mountain": {"value": "0", "color": wx.Colour(128, 128, 128)},
    "Land": {"value": "1", "color": wx.Colour(255, 165, 0)},
    "Water": {"value": "2", "color": wx.Colour(0, 0, 255)},
    "Sand": {"value": "3", "color": wx.Colour(255, 218, 185)},
    "Forest": {"value": "4", "color": wx.Colour(0, 128, 0)}
}

class MapApp(wx.Frame):
    def __init__(self, map_data):
        super(MapApp, self).__init__(None, title="Map Editor", size=(800, 600))
        self.map_data = map_data
        self.initUI()

    def initUI(self):
        panel = wx.Panel(self)
        grid = wx.GridSizer(len(self.map_data), len(self.map_data[0]), 10, 10)

        self.buttons = []
        for i, row in enumerate(self.map_data):
            button_row = []
            for j, cell in enumerate(row):
                terrain, state = cell
                btn = wx.Button(panel, label=state, size=(40, 40))
                btn.SetBackgroundColour(self.get_terrain_color(terrain))
                btn.Bind(wx.EVT_LEFT_DOWN, lambda event, x=i, y=j: self.on_left_click(event, x, y))
                btn.Bind(wx.EVT_RIGHT_DOWN, lambda event, x=i, y=j: self.on_right_click(event, x, y))
                grid.Add(btn, 0, wx.EXPAND)
                button_row.append(btn)
            self.buttons.append(button_row)

        panel.SetSizer(grid)
        self.Centre()

    def get_terrain_color(self, terrain):
        for key, attributes in TERRAINS.items():
            if attributes["value"] == terrain:
                return attributes["color"]
        return wx.Colour(255, 255, 255)  # Default white color

    def on_left_click(self, event, i, j):
        current_terrain, current_state = self.map_data[i][j]
        dlg = wx.TextEntryDialog(self, 'Enter values separated by commas:', 'Edit Cell', current_state)
        if dlg.ShowModal() == wx.ID_OK:
            new_state = dlg.GetValue()
            self.map_data[i][j] = (current_terrain, new_state)
            self.buttons[i][j].SetLabel(new_state)
        dlg.Destroy()

    def on_right_click(self, event, i, j):
        dlg = wx.SingleChoiceDialog(self, 'Choose terrain type:', 'Terrain Selection', list(TERRAINS.keys()))
        if dlg.ShowModal() == wx.ID_OK:
            selected_terrain = dlg.GetStringSelection()
            self.map_data[i][j] = (TERRAINS[selected_terrain]["value"], self.map_data[i][j][1])
            self.buttons[i][j].SetBackgroundColour(TERRAINS[selected_terrain]["color"])
            self.buttons[i][j].Refresh()
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
