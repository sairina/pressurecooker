import math
import tempfile
import numpy as np
import os
import wave
import subprocess
import sys
import matplotlib
import zipfile
import ebooklib
import ebooklib.epub
from io import BytesIO

# On OS X, the default backend will fail if you are not using a Framework build of Python,
# e.g. in a virtualenv.
# On Linux, the default backend will fail if tkinter is not installed.
# To avoid having to set MPLBACKEND each time we use Pressure Cooker, automatically set the backend.
matplotlib.use("PS")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backends.backend_agg import FigureCanvasAgg
from pdf2image import convert_from_path
from PIL import Image, ImageOps

from le_utils.constants import file_formats

from .thumbscropping import scale_and_crop



# SMARTCROP UTILS
################################################################################

THUMBNAIL_SIZE = (400, 225)  # 16:9

def scale_and_crop_thumbnail(image, size=THUMBNAIL_SIZE, crop="smart", **kwargs):
    """
    Scale and crop the PIL Image ``image`` to maximum dimensions of ``size``.
    By default, ``crop`` is set to "smart" which will crop the image down to size
    based on the entropy content of the pixels. The other options are:
    * Use ``crop="0,0"`` to crop from the left and top edges
    * Use ``crop=",0"`` to crop from the top edge.
    Optional keyword arguments:
    * ``zoom=X``: crop outer X% before starting
    * ``target``: recenter here before cropping (default center ``(50, 50)``)
    See the ``scale_and_crop`` docs in ``thumbscropping.py`` for more details.
    """
    return scale_and_crop(image, size, crop=crop, upscale=True, **kwargs)



# THUMBNAILS FOR CONTENT KINDS
################################################################################

def get_image_from_epub(epubfile, fpath_out, crop=None):
    book = ebooklib.epub.read_epub(epubfile)
    # 1. try to get cover image from book metadata (content.opf)
    cover_item = None
    covers = book.get_metadata('http://www.idpf.org/2007/opf', 'cover')
    if covers:
        cover_tuple = covers[0] # ~= (None, {'name':'cover', 'content':'item1'})
        assert cover_tuple[1]['name'] == 'cover', 'wrong key name'
        cover_item_id = cover_tuple[1]['content']
        for item in book.items:
            if item.id == cover_item_id:
                cover_item = item
    if cover_item:
        image_data = BytesIO(cover_item.get_content())
    else:
        # 2. fallback to get first image in the ePub file
        images = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))
        # TODO: get largest image of the bunch
        if not images:
            return
        image_data = BytesIO(images[0].get_content())

    # Save image_data to fpath_out
    im = Image.open(image_data)
    im = scale_and_crop_thumbnail(im, crop=crop)
    im.save(fpath_out)


def get_image_from_zip(htmlfile, fpath_out, crop="smart"):
    biggest_name = None
    size = 0
    with zipfile.ZipFile(htmlfile, 'r') as zf:
        valid_exts = [file_formats.PNG, file_formats.JPEG, file_formats.JPG]
        valid_files = filter(lambda f: os.path.splitext(f)[1][1:] in valid_exts, zf.namelist())
        # get the biggest (most pixels) image in the zip.
        for filename in valid_files:
            _, ext = os.path.splitext(filename)
            with zf.open(filename) as fhandle:
                image_data = fhandle.read()
            with BytesIO(image_data) as bhandle:
                img = Image.open(bhandle)
                img_size = img.size[0] * img.size[1]
                if img_size > size:
                    biggest_name = filename
                    size = img_size
        if not biggest_name:
            return None  # this zip has no images
        with zf.open(biggest_name) as fhandle:
            image_data = fhandle.read()
            with BytesIO(image_data) as bhandle:
                img = Image.open(bhandle)
                img = scale_and_crop_thumbnail(img, crop=crop)
                img.save(fpath_out)


def create_image_from_pdf_page(fpath_in, fpath_out, page_number=0, crop=None):
    """
    Create an image from the pdf at fpath_in and write result to fpath_out.
    """
    assert fpath_in.endswith('pdf'), "File must be in pdf format"
    pages = convert_from_path(fpath_in, 500, first_page=page_number, last_page=page_number+1)
    page = pages[0]
    # resize
    page = scale_and_crop_thumbnail(page, zoom=10, crop=crop)
    page.save(fpath_out, 'PNG')


def create_waveform_image(fpath_in, fpath_out, max_num_of_points=None, colormap_options=None):
    """
    Create a waveform image from audio or video file at fpath_in and write to fpath_out
    Colormaps can be found at http://matplotlib.org/examples/color/colormaps_reference.html
    """
    colormap_options = colormap_options or {}
    cmap_name = colormap_options.get('name') or 'cool'
    vmin = colormap_options.get('vmin') or 0
    vmax = colormap_options.get('vmax') or 1
    color = colormap_options.get('color') or 'w'

    tempwav_fh, tempwav_name = tempfile.mkstemp(suffix=".wav")
    os.close(tempwav_fh)  # close the file handle so ffmpeg can write to the file
    try:
        ffmpeg_cmd = ['ffmpeg', '-y', '-loglevel', 'panic', '-i', fpath_in]
        # The below settings apply to the WebM encoder, which doesn't seem to be built by Homebrew on Mac,
        # so we apply them conditionally.
        if not sys.platform.startswith('darwin'):
            ffmpeg_cmd.extend(['-cpu-used', '-16'])
        ffmpeg_cmd += [tempwav_name]
        subprocess.call(ffmpeg_cmd)

        spf = wave.open(tempwav_name, 'r')

        #Extract Raw Audio from Wav File
        signal = spf.readframes(-1)
        signal = np.frombuffer(signal, np.int16)

        # Get subarray from middle
        length = len(signal)
        count = max_num_of_points or length
        subsignals = signal[int((length-count)/2):int((length+count)/2)]

        # Set up max and min values for axes
        X = [[.6, .6], [.7, .7]]
        xmin, xmax = xlim = 0, count
        max_y_axis = max(-min(subsignals), max(subsignals))
        ymin, ymax = ylim = -max_y_axis, max_y_axis

        # Set up canvas according to user settings
        (xsize, ysize) = (THUMBNAIL_SIZE[0]/100.0, THUMBNAIL_SIZE[1]/100.0)
        figure = Figure(figsize=(xsize, ysize), dpi=100)
        canvas = FigureCanvasAgg(figure)
        ax = figure.add_subplot(111, xlim=xlim, ylim=ylim, autoscale_on=False, frameon=False)
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.set_xticks([])
        ax.set_yticks([])
        cmap = plt.get_cmap(cmap_name)
        cmap = LinearSegmentedColormap.from_list(
            'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=vmin, b=vmax),
            cmap(np.linspace(vmin, vmax, 100))
        )
        ax.imshow(X, interpolation='bicubic', cmap=cmap, extent=(xmin, xmax, ymin, ymax), alpha=1)

        # Plot points
        ax.plot(np.arange(count), subsignals, color)
        ax.set_aspect("auto")
        canvas.print_figure(fpath_out)

    finally:
        os.remove(tempwav_name)



# TILED THUMBNAILS FOR TOPIC NODES (FOLDERS)
################################################################################

def create_tiled_image(source_images, fpath_out):
    """
    Create a 16:9 tiled image from list of image paths provided in source_images
    and write result to fpath_out.
    """
    sizes = {1:1, 4:2, 9:3, 16:4, 25:5, 36:6, 49:7}
    assert len(source_images) in sizes.keys(), "Number of images must be a perfect square <= 49"
    root = sizes[len(source_images)]

    images = list(map(Image.open, source_images))
    new_im = Image.new('RGBA', THUMBNAIL_SIZE)
    offset = (int(float(THUMBNAIL_SIZE[0]) / float(root)),
              int(float(THUMBNAIL_SIZE[1]) / float(root)) )

    index = 0
    for y_index in range(root):
        for x_index in range(root):
            im = scale_and_crop_thumbnail(images[index], size=offset)
            new_im.paste(im, (int(offset[0] * x_index), int(offset[1] * y_index)))
            index = index + 1
    new_im.save(fpath_out)
