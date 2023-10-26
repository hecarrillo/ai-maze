import wx

TERRAINS = {
    "Mountain": {"value": "1", "color": wx.Colour(50, 50, 50)},
    "Land": {"value": "2", "color": wx.Colour(255, 218, 185)},
    "Water": {"value": "3", "color": wx.Colour(0, 0, 255)},
    "Sand": {"value": "4", "color": wx.Colour(255, 165, 0)},
    "Forest": {"value": "5", "color": wx.Colour(0, 255, 0)}
}

DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
DIRECTION_OF_LETTER = {'U':(-1,0), 'R':(0,1), 'D':(1,0), 'L':(0,-1)}

CHARACTERS = {
    "Human": {
        "Mountain": 1000,
        "Land": 1,
        "Water": 2,
        "Sand": 3,
        "Forest": 4
    },
    "Sasquatch": {
        "Mountain": 1,
        "Land": 1,
        "Water": 1000,  # Sasquatch can't cross water
        "Sand": 2,
        "Forest": 1
    },
    "Monkey": {
        "Mountain": 1000,
        "Land": 2,
        "Water": 4,
        "Sand": 3,
        "Forest": 1
    },
    "Octopus": {
        "Mountain": 1000,  # Octopus can't cross mountains
        "Land": 4,
        "Water": 1,
        "Sand": 1000,
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

OBJECTIVES = ("I", "D", "K", "P")
ROUTES = ("IP","IKP","IDP","IKDP","IDKP")