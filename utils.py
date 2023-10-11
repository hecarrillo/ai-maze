import networkx as nx

def hierarchy_pos(G, root=None, width=1., vert_gap=1, vert_loc=0, xcenter=0.5):
    """
    Compute the positions for nodes in a tree layout.

    :param G: NetworkX graph or list of nodes
    :param root: Root node for the tree layout
    :param width: Horizontal space allocated for the whole tree
    :param vert_gap: Gap between levels of the tree
    :param vert_loc: Vertical location of the root
    :param xcenter: Horizontal location of the root
    :return: Dictionary of positions {node: (x, y)}
    """

    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)

def _hierarchy_pos(G, root, width=1., vert_gap=1, vert_loc=0, xcenter=0.5, pos=None, parent=None, parsed=None):
    """
    Recursive function to compute the positions for nodes in a tree layout.

    :param G: NetworkX graph or list of nodes
    :param root: Root node for the tree layout
    :param width: Horizontal space allocated for the whole tree
    :param vert_gap: Gap between levels of the tree
    :param vert_loc: Vertical location of the root
    :param xcenter: Horizontal location of the root
    :param pos: Current positions of nodes
    :param parent: Parent node (used in recursion)
    :param parsed: List of nodes that have been parsed (used in recursion)
    :return: Dictionary of positions {node: (x, y)}
    """

    if parsed is None:
        parsed = []
    if pos is None:
        pos = {root: (xcenter, vert_loc)}
    else:
        pos[root] = (xcenter, vert_loc)
    children = list(G.neighbors(root))
    if not isinstance(G, nx.DiGraph) and parent is not None:
        children.remove(parent)
    if children:
        dx = width / len(children)
        nextx = xcenter - width/2 - dx/2
        for child in children:
            nextx += dx
            pos = _hierarchy_pos(G, child, width=dx, vert_gap=vert_gap, vert_loc=vert_loc-vert_gap, xcenter=nextx, pos=pos, parent=root, parsed=parsed)
    return pos

def read_map_from_file(filename):
    with open(filename, 'r') as file:
        return [[(char, "") for char in line.strip()] for line in file.readlines()]
