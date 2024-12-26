# STUMPY
# Copyright 2019 TD Ameritrade. Released under the terms of the 3-Clause BSD license.
# STUMPY is a trademark of TD Ameritrade IP Company, Inc. All rights reserved.

import ast
import importlib
import pathlib
import pkgutil
import site
import warnings

CACHE_WARNING = "Caching `numba` functions is purely for experimental purposes "
CACHE_WARNING += "and should never be used or depended upon as it is not supported! "
CACHE_WARNING += "All caching capabilities are not tested and may be removed/changed "
CACHE_WARNING += "without prior notice. Please proceed with caution!"


def get_njit_funcs():
    """
    Identify all njit functions

    Parameters
    ----------
    None

    Returns
    -------
    out : list
        A list of (`module_name`, `func_name`) pairs
    """
    pkg_dir = pathlib.Path(__file__).parent
    module_names = [name for _, name, _ in pkgutil.iter_modules([str(pkg_dir)])]

    njit_funcs = []

    for module_name in module_names:
        filepath = pathlib.Path(__file__).parent / f"{module_name}.py"
        file_contents = ""
        with open(filepath, encoding="utf8") as f:
            file_contents = f.read()
        module = ast.parse(file_contents)
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(
                        decorator.func, ast.Name
                    ):
                        if decorator.func.id == "njit":
                            njit_funcs.append((module_name, func_name))

    return njit_funcs


def _enable():
    """
    Enable numba caching

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    warnings.warn(CACHE_WARNING)
    njit_funcs = get_njit_funcs()
    for module_name, func_name in njit_funcs:
        module = importlib.import_module(f".{module_name}", package="stumpy")
        func = getattr(module, func_name)
        func.enable_caching()


def _clear():
    """
    Clear numba cache

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    warnings.warn(CACHE_WARNING)
    site_pkg_dir = site.getsitepackages()[0]
    numba_cache_dir = site_pkg_dir + "/stumpy/__pycache__"
    [f.unlink() for f in pathlib.Path(numba_cache_dir).glob("*nb*") if f.is_file()]


def _get_cache():
    """
    Retrieve a list of cached numba functions

    Parameters
    ----------
    None

    Returns
    -------
    out : list
        A list of cached numba functions
    """
    warnings.warn(CACHE_WARNING)
    site_pkg_dir = site.getsitepackages()[0]
    numba_cache_dir = site_pkg_dir + "/stumpy/__pycache__"
    return [f.name for f in pathlib.Path(numba_cache_dir).glob("*nb*") if f.is_file()]


def _recompile(func=None, fastmath=None):
    """
    Recompile a jit/njit decorated function. If `func` is None, then it will
    recompile all njit functions of STUMPY.

    Parameters
    ----------
    func : a njit function, default None
        The numba function to recompile. If None, then all njit functions
        of STUMPY will be recompiled.

    fastmath : bool or set, default None
        The fastmath flags to use. If None, then the func's fastmath flags
        will not be changed. This is only used when `func` is provided.

    Returns
    -------
    None
    """
    warnings.warn(CACHE_WARNING)

    njit_funcs = []
    for module_name, func_name in get_njit_funcs():
        module = importlib.import_module(f".{module_name}", package="stumpy")
        njit_funcs.append(getattr(module, func_name))

    recompile_funcs = []
    if func is None:
        recompile_funcs = njit_funcs
    elif func in njit_funcs:
        recompile_funcs.append(func)
    else:
        msg = "The function `func` is not a njit function in STUMPY"
        raise ValueError(msg)

    for func in recompile_funcs:
        if fastmath is not None:
            func.targetoptions["fastmath"] = fastmath
        func.recompile()

    return
