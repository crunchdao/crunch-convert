from typing import Optional

import libcst


def is_r_import(original_node: libcst.CSTNode) -> Optional[str]:
    is_assign = (
        isinstance(original_node, libcst.Assign)
        and len(original_node.targets) == 1
        and isinstance(original_node.targets[0].target, libcst.Name)
    )

    is_ann_assign = (
        isinstance(original_node, libcst.AnnAssign)
        and isinstance(original_node.target, libcst.Name)
    )

    if not (is_assign or is_ann_assign):
        return None

    call = original_node.value  # type: ignore
    if not isinstance(call, libcst.Call):
        return None

    func = call.func
    if not isinstance(func, libcst.Name):
        return None

    if func.value != "importr":
        return None

    if len(call.args) == 0:
        return None

    first_arg = call.args[0].value
    if not isinstance(first_arg, libcst.SimpleString):
        return None

    raw_string = first_arg.value
    if len(raw_string) <= 2:
        # only contains quotes
        return None

    return raw_string[1:-1]
