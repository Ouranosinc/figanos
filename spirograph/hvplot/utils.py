import json
import warnings
from importlib import resources
from itertools import groupby
from tkinter import font as tkfont
from typing import Any, Dict, Union

import xarray as xr


def wrap_title(font, font_size, txt, fig_size):
    ft = tkfont.Font(family=font, size=font_size, weight="bold")
    wid = [ft.measure(txt)]
    tit = [txt]
    while any(w > fig_size for w in wid):
        for v in range(0, len(wid)):
            val = tit[v]
            if ft.measure(val) > fig_size:
                sp = val.split(" ")
                mid = round(len(sp) / 2)

                # ici check pour pas split sur un symbole ou un nombre (comme tmax = 0)
                try:
                    while (
                        all(
                            [
                                sp[mid].isalpha(),
                                sp[mid + 1].isalpha(),
                                sp[mid - 1].isalpha(),
                            ]
                        )
                        is False
                    ):
                        mid += 1
                # TODO: What type of Exceptions can be raised here?
                except:  # noqa
                    mid = round(len(sp) / 2)

                tit[v:v] = [" ".join(sp[0:mid]), " ".join(sp[mid:])]
                tit.pop(v + len([sp[0:mid], sp[mid:-1]]))
                wid[v:v] = [
                    ft.measure(" ".join(sp[0:mid])),
                    ft.measure(" ".join(sp[mid:-1])),
                ]
                wid.pop(v + len([sp[0:mid], sp[mid:-1]]))

    return "\n".join(tit)


# pas certaine en fonction de quoi: variables, indicateurs (ex: delta et autre), est-ce que ca veut dire tous les noms
# doivent etre dans le fichier json ou devrait laisser le choix à l'utilisateur dans les options args?
def precision(data: xr.DataArray):
    """Insert title here.

    Parameters
    ----------
    data : xr.DataArray
    """
    with open("./spirograph/precision.json") as f:
        precision_conf = json.load(f)

    dc = dict()
    if "delta" in data.name:
        dc["yformatter"] = f"%.{precision_conf['variable']['delta']}f"
    elif data.name in precision_conf["variable"].keys():
        dc["yformatter"] = f"%.{precision_conf['variable'][data.name]}f"
    elif data.name.split("_")[0] in precision_conf["variable"].keys():
        dc["yformatter"] = f"%.{precision_conf['variable'][data.name.split('_')[0]]}f"
    elif (
        "units"
        in data.attrs.keys() & data.attrs["units"]
        in precision_conf["units"].keys()
    ):
        dc["yformatter"] = f"%.{precision_conf['units'][data.attrs['units']]}f"
    else:
        dc["yformatter"] = f"%.{precision_conf['default']}f"

    if (
        data.min() > 1000 or data.max() < 0.00001
    ):  # to use scientific notation or not #ToDo: check if works well or need improvement
        dc["yformatter"] = dc["yformatter"].replace("f", "e")
    return dc


# TODO : est-ce que fait une fonction pour ça ou fait juste considérer que les gens vont l'avoir translate avec xclim avant
def translate_xclim(data: xr.DataArray):
    """Insert title here.

    Parameters
    ----------
    data: xr.DataArray

    """

    # with resources.open_text("xclim.data", "fr.json") as file:
    #     infer_translate = json.load(file)

    # french = infer_translate[data.name.upper()]

    # apres commment aller chercher les threshs surement dispo déja avec fonction xclim pcq long en terme de traduction
    # demander de l'aide a trevro ou pascal
    return None


def convert_dict_metadata(
    data: Union[dict[str, Any], xr.DataArray], metadata: Dict[str, Any], language: str
):
    """Return dict containing the figure elements to corresponding data metadata values

    Parameters
    ----------
    data: DataArray or Dict
        if DataArray looks for info in attributes
        if dict uses info directly, allows to use a combination of DataArray + Dataset attributes
    metadata: dict
        keys = figures elements (ex:title), values= metadata keys (ex: units, long_name)
    language: {"english", "french"}
        Language used in metadata.
    """

    if language == "french":
        for k, v in metadata.items():
            metadata[k] = v + "_fr"

    dct = {}
    if type(data) != dict:
        for k, v in metadata.items():
            if k == "title":
                dct[k] = wrap_title(
                    "Arial", 12, data.attrs[v], 700
                )  # ToDo: ajouter les infos du template pour les titres (soit dans les arguments ou direct dans la fonction)
            elif k == "ylabel" and "units" not in v and "units" in data.attrs:
                dct[k] = f"{data.attrs[v]} ({data.attrs['units']})"
            else:
                dct[k] = data.attrs[
                    v
                ]  # ToDO: add translate option if not already done et sortir la fonction dans utils
    else:
        for k, v in metadata.items():
            if k == "title":
                dct[k] = wrap_title(
                    "Arial", 12, data[v], 700
                )  # ToDo: ajouter les infos du template pour les titres (soit dans les arguments ou direct dans la fonction)
            elif k == "ylabel" and "units" not in v and "units" in data:
                dct[k] = f"{data[v]} ({data['units']})"
            else:
                dct[k] = data[v]

    return dct


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def reverse_color(cmap):
    if "_r" in cmap:
        return cmap.replace("_r", "")
    else:
        return cmap + "_r"


def posi_negative(data, cols):
    pos = data >= 0
    neg = data <= 0

    if pos.all().item():
        return cols[1]
    elif neg.all().item():
        return cols[2]
    else:
        return cols[0]


def colors_style(data: xr.DataArray, fig_type: str, id: int = 0):
    """Returns colors depending on type of plot (timeserie, colormap) and variables.

    Parameters
    ----------
    data : xr.DataArray
        xarray DataArray object.
    fig_type : {"colormap", "temperal_serie"}
        Figure type.
    id : int
        plot # (if more than one plot on the figure) default 0
    """

    with open("./spirograph/colors.json") as f:
        colors = json.load(f)

    dc_col_style = {}

    if fig_type == "temporal_serie":
        if "mean" in data.name.lower():
            dc_col_style["line_width"] = 3.5
        else:
            dc_col_style["line_width"] = 2
        if "experiment" in data.attrs or "experiment" in data.coords:
            if "rcp" in data.attrs["experiment"]:
                va = "rcp"
            else:
                va = "ssp"

            if "experiment" in data.coords:
                # FIXME: experiement - typo
                dc_col_style["color"] = colors[va][data.coords["experiement"]]
            else:
                dc_col_style["color"] = colors[va][data.coords["experiement"]]
        else:
            dc_col_style["color"] = colors["lines"][id]

    elif fig_type == "colormap":
        if (
            "deltas" in data.name
        ):  # est-ce que delta apparaît dans le nom de la data_variables, history, long_name...
            ind = "deltas"
        else:
            ind = "var_ind"

        if data.name in list(colors[ind].keys()):
            cmap = colors[ind][data.name]
        else:
            if "history" not in data.attrs:
                warnings.warn("Default colors chosen since variable not in colors.json")
                cmap = colors[ind]["default"]

            variables = [v for v in data.history.split(": \n") if "[" not in v]

            if len(variables) != 1:
                equal = all_equal(
                    [v[:2] for v in variables]
                )  # check si dataarray provient tu même genre de variable
                # avec deux premières lettres (ex: ta pour tas / tasmin / tasmax ou pr prtot prctot,..)

                if equal:
                    var_cols = [
                        v for v in variables if v in colors["deltas"]
                    ]  # variables qui ont une couleur associée, prend direct la premiere
                    cmap = colors[ind][var_cols[0]]
                else:
                    warnings.warn(
                        "Default colors chosen since indicator calculated from multiple variables not in colors.json"
                    )
                    cmap = colors[ind]["default"]
        if ind == "deltas":
            dc_col_style["cmap"] = posi_negative(data, cmap)
        else:
            dc_col_style["cmap"] = cmap[0]

    return dc_col_style


def perc_min_max(xr):
    return xr.coords["percentiles"].min().item(), xr.coords["percentiles"].max().item()


def ts_ens_title(data: xr.DataArray, metadata: Dict[str, Any], language: str):
    """Insert title here.

    Parameters
    ----------
    data: xr.DataArray
    metadata: dict
    language: {"english", "french"}

    """
    tit1 = data.attrs[metadata["title"]]
    if "percentiles" in data.coords:
        pmin, pmax = perc_min_max(data)
        if language == "english":
            title = tit1 + f" {pmin} to {pmax}  percentile of ensemble."
        elif language == "french":
            title = tit1 + f" {pmin} à {pmax}  centiles de l'ensemble."
        else:
            raise NotImplementedError(f"Language: {language}.")
    elif (
        "Dataset" in str(type(data))
        and sum(["_min" in v or "_max" in v for v in list(data.keys())]) == 2
    ):
        if language == "english":
            title = tit1 + " Minimum - maximum of ensemble."
        elif language == "french":
            title = tit1 + " Minimum - maximum de l'ensemble."
        else:
            raise NotImplementedError(f"Language: {language}.")
    else:
        raise RuntimeError()

    return wrap_title(
        "Arial", 12, title, 700
    )  # ToDo: ajouter les infos du template pour les titres (soit dans les arguments ou direct dans la fonction)


def ts_ens_label(
    data: xr.DataArray,
    metadata: Dict[str, Any],
    hv_kwargs: Dict[str, Any],
    language: str,
):
    """Insert title here.

    Parameters
    ----------
    data: xr.DataArray
    metadata: dict
    hv_kwargs: dict
    language: {"english", "french"}

    """
    if "label" in hv_kwargs:
        lab = hv_kwargs["label"]
    elif "label" in metadata:
        lab = data.attrs[metadata["label"]]

    ls_lab = []
    if "percentiles" in data.coords:
        pmin, pmax = perc_min_max(data)
        if language == "english":
            ls_lab[0] = f"p{pmin}th - p{pmax}th percentile " + lab
        elif language == "french":
            ls_lab[0] = f"{pmin} - {pmax} centiles " + lab
        if 50 in data.percentiles:
            if language == "french":
                ls_lab[1] = "median " + lab
            elif language == "english":
                ls_lab[1] = "médiane " + lab
    elif (
        "Dataset" in str(type(data))
        and sum(["_min" in v or "_max" in v or "_mean" in v for v in list(data.keys())])
        == 3
    ):
        if language == "english":
            ls_lab[0] = "ensemble of " + lab
            ls_lab[1] = "mean of " + lab
        elif language == "french":
            ls_lab[0] = "ensemble de " + lab
            ls_lab[1] = "moyenne de " + lab
    return ls_lab


def wrap_metdata(
    da: xr.DataArray,
    language: str,
    dict_metadata: Dict[str, Any],
    hv_kwargs: Dict[str, Any],
    ds_attrs: Dict[str, Any],
):
    """Insert title here.

    Parameters
    ----------
    da: xr.DataArray
    language: {"english", "french"}
    dict_metadata: dict
    hv_kwargs: dict
    ds_attrs: dict
    """
    if ds_attrs is not None:
        full_attr = {**da.attrs, **ds_attrs}
        args = {
            **hv_kwargs,
            **convert_dict_metadata(full_attr, dict_metadata, language),
            **precision(da),
        }
    else:
        args = {
            **hv_kwargs,
            **convert_dict_metadata(da, dict_metadata, language),
            **precision(da),
        }
    return args


# ToDo:  fonction qui transforme lat/lon en systeme -90:90 & -180:180
# est-ce que nécesaire ou xclim s'en occupe pas mal tout le temps?
