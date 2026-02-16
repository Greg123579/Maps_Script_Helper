# Example: Gaussian denoise first test
# Supports PNG, JPG, TIFF, and other formats
from skimage import io, img_as_ubyte
from skimage.filters import gaussian
import glob

# Find input image (supports .png, .jpg, .tif, etc.)
input_files = glob.glob("/input/image.*")
img_path = input_files[0] if input_files else "/input/image.png"
img = io.imread(img_path)
res = img_as_ubyte(gaussian(img, sigma=1.0, channel_axis=-1 if img.ndim==3 else None))
io.imsave("/output/result.png", res)
print("done")