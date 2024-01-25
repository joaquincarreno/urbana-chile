from matplotlib.collections import PatchCollection
from matplotlib.colors import from_levels_and_colors
from matplotlib.patches import Polygon, Patch
from mpl_toolkits.axes_grid1 import make_axes_locatable

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# from geopandas
def __pysal_choro(values, scheme, k=5):
    """
    Wrapper for choropleth schemes from PySAL for use with plot_dataframe
    Parameters
    ----------
    values
        Series to be plotted
    scheme : str
        One of pysal.esda.mapclassify classification schemes
        Options are 'Equal_interval', 'Quantiles', 'Fisher_Jenks'
    k : int
        number of classes (2 <= k <=9)
    Returns
    -------
    binning
        Binning objects that holds the Series with values replaced with
        class identifier and the bins.
    """
    try:
        from mapclassify import (
            Quantiles, EqualInterval, FisherJenks, UserDefined)
        schemes = {}
        schemes['equal_interval'] = EqualInterval
        schemes['quantiles'] = Quantiles
        schemes['fisher_jenks'] = FisherJenks
        schemes['user_defined'] = UserDefined
        scheme = scheme.lower()
        if scheme not in schemes:
            raise ValueError("Invalid scheme. Scheme must be in the"
                             " set: %r" % schemes.keys())
        binning = schemes[scheme](values, k)
        return binning
    except ImportError:
        raise ImportError("PySAL is required to use the 'scheme' keyword")


def feature_to_patch(s):
    s_arr = np.array(s.exterior.xy).T
    return Polygon(s_arr, closed=False)

def colorbar(ax, collection, orientation='vertical', percent=3, **cbar_kws):
    divider = make_axes_locatable(ax)
    position = 'right' if orientation == 'vertical' else 'bottom'
    label = cbar_kws.pop('label', None)
    cax = divider.append_axes(position, size="{}%".format(percent), pad=0.05)
    cbar = plt.colorbar(collection, cax=cax, orientation=orientation, **cbar_kws)
    cbar.set_label(label)
    return cbar

def choropleth(geodf, figsize=12, column=None, scheme='fisher_jenks',
                   user_bins=None,
                   n_colors=5, palette='viridis', alpha=0.75, cbar_orientation='vertical',
                   img_interpolation='hanning', cbar_fig_position=None, cbar_label=None, z=None, cbar_kws=None):

    bounds = geodf.total_bounds
    aspect = (bounds[2] - bounds[0]) / (bounds[3] - bounds[1])
    fig = plt.figure(figsize=(figsize, figsize / aspect))

    ax = plt.gca()
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    ax.set_aspect(1)

    plt.axis('off')

    cbar_kws = cbar_kws if cbar_kws else {}

    choro = []
    patch_values = []

    for idx, row in geodf.iterrows():
        feature = row.geometry
        value = row[column]

        if feature.geom_type == 'Polygon':
            choro.append(feature_to_patch(feature))
            patch_values.append(value)
        elif feature.geom_type == 'MultiPolygon':
            for subfeature in feature.geoms:
                choro.append(feature_to_patch(subfeature))
                patch_values.append(value)
        else:
            continue

    binning = __pysal_choro(geodf[column], scheme=scheme, k=n_colors if scheme != 'user_defined' else user_bins)
    if scheme != 'user_defined':
        bins = np.insert(binning.bins, 0, geodf[column].min())
    else:
        bins = binning.bins

    palette_values = sns.color_palette(palette, n_colors=n_colors)
    cmap, norm = from_levels_and_colors(bins, palette_values, extend='neither')
    cmap.set_over(palette_values[-1], alpha=alpha)

    collection = PatchCollection(choro, linewidth=1, edgecolor='white', alpha=alpha, cmap=cmap, norm=norm)
    collection.set_array(np.array(patch_values))

    cbar_label = cbar_label if cbar_label is not None else column

    cbar_kws = dict(shrink=0.5, label=cbar_label, ticks=bins)
    colorbar(ax, collection, orientation=cbar_orientation, **cbar_kws)

    ax.add_collection(collection)
    plt.tight_layout()
    return ax
