#!/usr/bin/env python

import argparse
import ast
import importlib
import pathlib


def get_njit_funcs():
    """
    Identify all njit functions

    Parameters
    ----------
    None

    Returns
    -------
    njit_funcs : list
        A list of all njit functions, where each element is a tuple of the form
        (module_name, func_name)
    """
    ignore_py_files = ["__init__", "__pycache__"]

    pkg_dir = pathlib.Path(__file__).parent / "stumpy"
    module_names = []
    for fname in pkg_dir.iterdir():
        if fname.stem not in ignore_py_files and not fname.stem.startswith("."):
            module_names.append(fname.stem)

    njit_funcs = []
    for module_name in module_names:
        filepath = pkg_dir / f"{module_name}.py"
        file_contents = ""
        with open(filepath, encoding="utf8") as f:
            file_contents = f.read()
        module = ast.parse(file_contents)
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                for decorator in node.decorator_list:
                    decorator_name = None

                    if isinstance(decorator, ast.Name):
                        # Bare decorator
                        decorator_name = decorator.id
                    if isinstance(decorator, ast.Call) and isinstance(
                        decorator.func, ast.Name
                    ):
                        # Decorator is a function
                        decorator_name = decorator.func.id

                    if decorator_name == "njit":
                        njit_funcs.append((module_name, func_name))

    return njit_funcs


def check_fastmath():
    """
    Check if all njit functions have the `fastmath` flag set

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    missing_fastmath = []  # list of njit functions with missing fastmath flags
    for module_name, func_name in get_njit_funcs():
        module = importlib.import_module(f".{module_name}", package="stumpy")
        func = getattr(module, func_name)
        if "fastmath" not in func.targetoptions.keys():
            missing_fastmath.append(f"{module_name}.{func_name}")

    if len(missing_fastmath) > 0:
        msg = (
            "Found one or more `@njit` functions that are missing the `fastmath` flag. "
        )
        msg += f"The function(s) are:\n {missing_fastmath}\n"
        raise ValueError(msg)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        check_fastmath()
