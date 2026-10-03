"""Uniform grid for fast neighbour queries."""

from . import config as C


class Grid:
    """Spatial hash that buckets entities into square cells by their bounding box."""

    def __init__(self, cell: int = C.GRID_CELL):
        self.cell = cell
        self.cells: dict[tuple[int, int], list] = {}

    def clear(self) -> None:
        """Remove all entities."""
        self.cells.clear()

    def insert(self, ent) -> None:
        """Add an entity to every cell its bounding box overlaps."""
        c = self.cell
        r = ent.radius
        x0, x1 = int((ent.x - r) // c), int((ent.x + r) // c)
        y0, y1 = int((ent.y - r) // c), int((ent.y + r) // c)
        cells = self.cells
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                lst = cells.get((cx, cy))
                if lst is None:
                    cells[(cx, cy)] = [ent]
                else:
                    lst.append(ent)

    def query(self, x: float, y: float, r: float) -> list:
        """Return entities whose cells overlap the box around (x, y, r).

        The result may contain duplicates.
        """
        c = self.cell
        x0, x1 = int((x - r) // c), int((x + r) // c)
        y0, y1 = int((y - r) // c), int((y + r) // c)
        out = []
        cells = self.cells
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                lst = cells.get((cx, cy))
                if lst:
                    out.extend(lst)
        return out

    def query_unique(self, x: float, y: float, r: float) -> list:
        """Return entities near (x, y, r) like `query`, without duplicates."""
        seen = set()
        out = []
        for e in self.query(x, y, r):
            i = id(e)
            if i not in seen:
                seen.add(i)
                out.append(e)
        return out
