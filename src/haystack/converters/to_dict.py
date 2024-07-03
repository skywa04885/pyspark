from collections import OrderedDict
from typing import Any, Dict, List, Optional, OrderedDict as OrderedDictT
from ztypes import HBool, HDate, HDateTime, HGrid, HNum, HRef, HSymbol, HTime, HVal

def _encode_hval(hval: HVal) -> Any:
    if (
        isinstance(hval, HDateTime)
        or isinstance(hval, HDate)
        or isinstance(hval, HTime)
        or isinstance(hval, HBool)
        or isinstance(hval, HRef)
        or isinstance(hval, HSymbol)
    ):
        return hval.val
    elif isinstance(hval, HNum):
        if hval.unit is not None:
            return f"{hval.val}{hval.unit}"
        else:
            return hval.val

    return None

def haystack_grid_to_dict(grid: HGrid, use_name: bool = True) -> OrderedDictT[str, List[Any]]:
    val: OrderedDictT[str, List[Any]] = OrderedDict()

    for hcoli, hcol in enumerate(grid.cols):
        col: List[Any] = []

        for hrow in grid.rows:
            col.append(_encode_hval(hrow[hcoli]))

        val[hcol.name] = col

    return val
