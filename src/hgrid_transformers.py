from typing import Any, Dict, List
import pandas

from ztypes import HBool, HGrid, HMarker, HNa, HNull, HNum, HRef, HStr, HSymbol, HUri

class HGridTransformers:
    @staticmethod
    def into_dataframe(hgrid: HGrid) -> pandas.DataFrame:
        cols: Dict[str, List[Any]] = {}

        for i, col in enumerate(hgrid.cols):
            cells: List[Any] = []

            for grid_row in hgrid.rows:
                grid_cell = grid_row[i]

                if isinstance(grid_cell, HNum):
                    cells.append(grid_cell.val)
                elif isinstance(grid_cell, HBool):
                    cells.append(grid_cell.val)
                elif isinstance(grid_cell, HStr):
                    cells.append(grid_cell.val)
                elif isinstance(grid_cell, HUri):
                    cells.append(grid_cell.val)
                elif isinstance(grid_cell, HSymbol):
                    cells.append(grid_cell.val)
                elif isinstance(grid_cell, HRef):
                    cells.append(grid_cell.val)
                elif isinstance(grid_cell, HRef):
                    cells.append(grid_cell.val)
                elif isinstance(grid_cell, HMarker):
                    cells.append("$M")
                elif isinstance(grid_cell, HMarker):
                    cells.append("$R")
                elif isinstance(grid_cell, HNa):
                    cells.append("$NA")
                elif isinstance(grid_cell, HNull):
                    cells.append(None)
                else:
                    cells.append(None)


            cols[col.name] = cells

        return pandas.DataFrame(cols)