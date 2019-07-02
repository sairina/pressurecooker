import os
import pytest

import PIL
from pressurecooker import images

tests_dir = os.path.dirname(os.path.abspath(__file__))
files_dir = os.path.join(tests_dir, 'files')
outputs_dir = os.path.join(files_dir, 'expected_output')

# these settings are chosen to match our current use case in Studio
studio_cmap_options = {'name': 'BuPu', 'vmin': 0.3, 'vmax': 0.7, 'color': 'black'}


SHOW_THUMBS = False     # set to True to show outputs when running tests locally



class BaseThumbnailGeneratorTestCase(object):

    def check_thumbnail_generated(self, output_file):
        """
        Checks that a thumbnail file at output_file exists and not too large.
        """
        assert os.path.exists(output_file)
        im = PIL.Image.open(output_file)
        width, height = im.size
        if SHOW_THUMBS: im.show()
        assert width < 1000, 'thumbnail generated is too large (w >= 1000)'
        assert height < 1000, 'thumbnail generated is too tall (h >= 1000)'
        return im

    def check_16_9_format(self, output_file):
        """
        Checks that a thumbnail file at output_file exists and not too large,
        and roughly in 16:9 aspect ratio.
        """
        assert os.path.exists(output_file)
        im = PIL.Image.open(output_file)
        width, height = im.size
        assert float(width)/float(height) == 16.0/9.0
        if SHOW_THUMBS: im.show()
        return im



class Test_wavefile_thumbnail_generation(BaseThumbnailGeneratorTestCase):

    def test_generates_16_9_thumbnail(self, tmpdir):
        input_file = os.path.join(files_dir, 'Wilhelm_Scream.mp3')
        assert os.path.exists(input_file)
        thumbnail_name = 'Wilhelm_Screen_thumbnail.png'
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.create_waveform_image(input_file, output_file, colormap_options=studio_cmap_options)
        self.check_16_9_format(output_file)
        # TODO: Store the expected output and compare the contents to the generated file?



class Test_pdf_thumbnail_generation(BaseThumbnailGeneratorTestCase):

    def test_generates_thumbnail(self, tmpdir):
        input_file = os.path.join(files_dir, "demo.pdf")
        assert os.path.exists(input_file)
        thumbnail_name = "pdf.png"
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.create_image_from_pdf_page(input_file, output_file)
        self.check_thumbnail_generated(output_file)

    def test_generates_16_9_thumbnail(self, tmpdir):
        input_file = os.path.join(files_dir, "demo.pdf")
        assert os.path.exists(input_file)
        thumbnail_name = "pdf_16_9.png"
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.create_image_from_pdf_page(input_file, output_file, crop='smart')
        self.check_16_9_format(output_file)



class Test_HTML_zip_thumbnail_generation(BaseThumbnailGeneratorTestCase):

    def test_generates_16_9_thumbnail(self, tmpdir):
        input_file = os.path.join(files_dir, 'thumb.zip')
        assert os.path.exists(input_file)
        thumbnail_name = 'zipfile.png'
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.get_image_from_zip(input_file, output_file)
        im = self.check_16_9_format(output_file)
        # check is blue image
        r, g, b = im.getpixel((1, 1))
        assert b>g and b>r, (r,g,b)



class Test_tiled_thumbnail_generation(BaseThumbnailGeneratorTestCase):

    def test_generates_brazil_thumbnail(self, tmpdir):
        input_file = os.path.join(files_dir, 'thumbnails/BRAlogo1.png')
        assert os.path.exists(input_file)
        input_files = [input_file, input_file, input_file, input_file]
        thumbnail_name = 'tiled.png'
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.create_tiled_image(input_files, output_file)
        self.check_16_9_format(output_file)
        # TODO: Store the expected output and compare the contents to the generated file?

    def test_generates_kolibris_thumbnail(self, tmpdir):
        filenames = ['BRAlogo1.png', 'toosquare.png', 'tootall.png', 'toowide.png']
        input_files = []
        for filename in filenames:
            input_file = os.path.join(files_dir, 'thumbnails', filename)
            assert os.path.exists(input_file)
            input_files.append(input_file)
        thumbnail_name = 'tiled.png'
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.create_tiled_image(input_files, output_file)
        self.check_16_9_format(output_file)
        # TODO: Store the expected output and compare the contents to the generated file?



class Test_epub_thumbnail_generation(BaseThumbnailGeneratorTestCase):

    def test_generates_thumbnail(self, tmpdir):
        input_file = os.path.join(files_dir, 'epub.epub')
        assert os.path.exists(input_file)
        thumbnail_name = 'epub.png'
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.get_image_from_epub(input_file, output_file)
        self.check_thumbnail_generated(output_file)

    def test_generates_16_9_thumbnail(self, tmpdir):
        input_file = os.path.join(files_dir, 'epub.epub')
        assert os.path.exists(input_file)
        thumbnail_name = 'epub_16_9.png'
        output_path = tmpdir.join(thumbnail_name)
        output_file = output_path.strpath
        images.get_image_from_epub(input_file, output_file, crop=",0") #crop='smart')
        self.check_16_9_format(output_file)
