"""Uniform grid for fast neighbour queries."""

from . import config as C


class Grid:
    def __init__(self, cell: int = C.GRID_CELL):
        self.cell = cell
        self.cells: dict[tuple[int, int], list] = {}

    def clear(self) -> None:
        self.cells.clear()

    def insert(self, ent) -> None:
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
        """Entities whose cells overlap the box around (x, y, r). May contain duplicates."""
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
        seen = set()
        out = []
        for e in self.query(x, y, r):
            i = id(e)
            if i not in seen:
                seen.add(i)
                out.append(e)
        return out
