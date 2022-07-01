import os
import tqdm
import numpy as np
import xarray as xr
from scipy.spatial import KDTree
from PIL import Image

from lltiler.lltiler import resolution2zoom, render_tile, numTiles


def ll2xyz(lat, lon):
    lat = np.deg2rad(lat)
    lon = np.deg2rad(lon)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)


class TileIndexBuilder:
    def __init__(self, xyz_coords):
        self.tree = KDTree(xyz_coords)

    def ll2index(self, lat, lon):
        xyz = ll2xyz(lat, lon)
        d, i = self.tree.query(xyz, workers=-1)
        return i

    def generate_index(self, level, tilesize):
        idxs = np.zeros((numTiles(level), numTiles(level), tilesize, tilesize), dtype="u4")
        for i in tqdm.tqdm(list(range(numTiles(level)))):
            for j in range(numTiles(level)):
                idxs[i, j] = render_tile(i, j, level, self.ll2index, tilesize)

        return xr.Dataset({
        f"{self.element_type}_of_pixel": (("tx", "ty", "y", "x"), idxs, {
            "start_index": 0,
            "long_name": f"0-based index of nearest neighbor grid {self.element_type} to map tile",
        })},
        attrs={
            "tile_level": level,
            "tilesize": tilesize,
        })


class CellTileIndexBuilder(TileIndexBuilder):
    element_type = "cell"
    def __init__(self, grid):
        super().__init__(np.stack([grid["cell_circumcenter_cartesian_" + i] for i in "xyz"], axis=1))

        
# ---


def sel_2nd(tiles, ix, iy):
    return (tiles
            .isel(tx=slice(ix, None, 2), ty=slice(iy, None, 2))
            .assign_coords(tx=tiles.tx[::2]//2, ty=tiles.ty[::2]//2))


def pyramid_step(tiles):
    return (xr.concat([xr.concat([sel_2nd(tiles, 0, 0), sel_2nd(tiles, 1, 0)], dim="x"),
                       xr.concat([sel_2nd(tiles, 0, 1), sel_2nd(tiles, 1, 1)], dim="x")],
                      dim="y")
            .coarsen(x=2, y=2)
            .mean()
            .assign_coords(x=tiles.x, y=tiles.y)
            .chunk({"tx": 4, "ty": 4, "x": len(tiles.x), "y": len(tiles.y)}))


def store_raw_tiles(tiles, folder):
    tileds = xr.Dataset({"tiles": tiles})
    level = int(np.log2(tileds.dims["tx"]))
    print("storing raw tiles")
    while level >= 0:
        filename = os.path.join(folder, f"{level}.zarr")
        print(f".. level {level}")
        tileds.to_zarr(filename)
        if level > 0:
            tileds = pyramid_step(xr.open_zarr(filename, chunks={"tx": 8, "ty": 8}))
        level = level - 1


def build_raw_tiles(var, index, folder):
    values = var.values
    
    def get(x):
        return xr.DataArray(values[x.values], dims=x.dims)
    
    tiles = (xr.map_blocks(get, index)
             .assign_coords(**{name: np.arange(size)
                               for name, size in zip(index.dims, index.shape)})
             .assign_attrs(var.attrs))
    
    store_raw_tiles(tiles, folder)


def build_image_tiles(rawfolder, targetfolder, norm, cmap, maxlevel):
    print("storing image tiles")
    for level in range(maxlevel+1):
        prefix = f"{targetfolder}/{level}/"

        def store_images(block):
            for itx, tx in enumerate(block.tx.values):
                for ity, ty in enumerate(block.ty.values):
                    name = f"{tx}/{ty}.jpg"
                    im = Image.fromarray(cmap(norm(block.isel(tx=itx, ty=ity)), bytes=True)[..., :3])
                    filename = os.path.join(prefix, name)
                    os.makedirs(os.path.dirname(filename), exist_ok=True)
                    im.save(filename)
            return block.tx * block.ty

        print(f".. level {level}")
        ds = xr.open_zarr(os.path.join(rawfolder, f"{level}.zarr"))
        run = xr.map_blocks(store_images, ds.tiles)
        run.compute()