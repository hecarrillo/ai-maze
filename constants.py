import wx

TERRAINS = {
    "Mountain": {"value": "2", "color": wx.Colour(0, 255, 0)},
    "Land": {"value": "1", "color": wx.Colour(255, 165, 0)},
    "Water": {"value": "0", "color": wx.Colour(0, 0, 255)},
    "Sand": {"value": "3", "color": wx.Colour(255, 218, 185)},
    "Forest": {"value": "4", "color": wx.Colour(0, 128, 0)}
}

DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
DIRECTION_OF_LETTER = {'U':(-1,0), 'R':(0,1), 'D':(1,0), 'L':(0,-1)}

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
    "Visited": "V",
    "Human": "H",
    "Octopus": "O",
    "Dark Temple": "D",
    "Portal Key": "K",
    "Portal": "P"
}
