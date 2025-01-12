import shapely.plotting
import matplotlib.pyplot as plt

def plot_two_polys(polys1: shapely.Polygon, polys2: shapely.Polygon, title: str = "No title") -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for poly in polys1:
        shapely.plotting.plot_polygon(poly, ax1)

    for poly in polys2:
        shapely.plotting.plot_polygon(poly, ax2)
    fig.suptitle("Set ID: " + str(title))