import numpy as np
import imageio
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter
from scipy.ndimage import grey_opening
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
import time
import mrcfile
import os

# --- Configuration ---
img_path = "/home/agarcia/develops/HoleIceBreaker/holes/HoleCrop_DandeyV_1.png"
img_path = "/home/agarcia/develops/HoleIceBreaker/holes/FRO30_3_square133_hole11.mrc"
#img_path = "/home/agarcia/develops/HoleIceBreaker/holes/FRO30_3_square133_hole19.mrc"
#img_path = "/home/agarcia/develops/HoleIceBreaker/holes/FRO30_3_square133_hole28.mrc"
#img_path = "/home/agarcia/develops/HoleIceBreaker/holes/LH11_3_square386_hole114.mrc"
#img_path = "/home/agarcia/develops/HoleIceBreaker/holesSquare/holeSquareDandeyV.png"
img_path = "/home/agarcia/develops/HoleIceBreaker/holesSquare/holeSquareDandeyV_2.png" #pavlov
img_path = "/data/agarcia/HoleIceBreaker/holesSquare/holeSquareDandeyV_2.png"#hertz-cinco
#img_path = "/data/agarcia/HoleIceBreaker/holesSquare/G2_square110_hole173.mrc" #hertz-cinco

#PIXEL_NEIGHBOR = 20 #Critical time cost (80->13 secs 50-> 6 secs
BIN_LEVELS = 5
SIGMA_GAUSSIAN = 3
RADIUS = 60

# --- Detect circle center using scipy ---
def detect_circle_center_scipy(img, radius_estimate, sigma=5):
    """
    Detect the center of a bright or dark circular object using edge detection and centroid optimization.
    """
    # Step 1: Smooth and detect edges
    smoothed = gaussian_filter(img, sigma=sigma)
    edges = np.gradient(smoothed)
    edge_magnitude = np.hypot(edges[0], edges[1])
    edge_binary = edge_magnitude > edge_magnitude.mean() + edge_magnitude.std()

    # Step 2: Get coordinates of edges
    y_coords, x_coords = np.nonzero(edge_binary)

    # Step 3: Define loss: sum of squared differences between radius and distance from (cx, cy)
    def circle_loss(center):
        cx, cy = center
        distances = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
        return np.mean((distances - radius_estimate)**2)

    # Step 4: Minimize loss
    h, w = img.shape
    initial_guess = (w // 2, h // 2)
    result = minimize(circle_loss, initial_guess, method='Powell')

    return tuple(map(int, result.x))  # Return as integer coordinates

# --- function to mask outside the circle ---
def mask_outside_circle(img, center=None, radius=None):
    """Masks the image outside a circular region."""
    h, w = img.shape
    if center is None:
        center = (w // 2, h // 2)
    if radius is None:
        radius = min(center[0], center[1], w - center[0], h - center[1])
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y - center[1])**2)
    mask = dist_from_center <= radius
    masked_img = img.copy()
    masked_img[~mask] = 0
    return masked_img

# --- function to get the actual intensity range ---
def get_intensity_range(img_masked):
    """Gets the min and max intensity values from the masked (non-zero) area."""
    pixels = img_masked[img_masked > 0]
    return pixels.min(), pixels.max()

# --- function to create bins and levels ---
def create_bins_levels(min_val, max_val, n_levels=5):
    """Creates quantization bins and levels based on the intensity range."""
    bins = np.linspace(min_val, max_val, n_levels + 1)
    levels = (bins[:-1] + bins[1:]) / 2
    levels = levels.astype(np.uint8)
    bins = bins.astype(np.uint8)
    return bins, levels

# --- quantize function ---
def quantize(image, bins, levels):
    """Quantizes the image into a smaller number of intensity levels."""
    quantized = np.zeros_like(image)
    for i in range(len(levels)):
        mask = (image >= bins[i]) & (image < bins[i+1])
        quantized[mask] = levels[i]
    # Ensure the maximum value is included in the last bin
    quantized[image == bins[-1]] = levels[-1]
    return quantized

# --- MAIN ---

# Dictionary to store execution times
execution_times = {}

# Load the image
ext = os.path.splitext(img_path)[1].lower()
if ext == '.mrc':
    with mrcfile.open(img_path, permissive=True) as mrc:
        img_data = mrc.data.copy()
        img = ((img_data - img_data.min()) / (img_data.max() - img_data.min()) * 255).astype(np.uint8)
else:
    img = imageio.imread(img_path, mode='L')

# Mask outside the circle
start_time = time.time()
# img_masked = mask_outside_circle(img,radius=RADIUS)
center = detect_circle_center_scipy(img, radius_estimate=RADIUS)
img_masked = mask_outside_circle(img, center=center, radius=RADIUS)
execution_times['mask_outside_circle'] = time.time() - start_time


# Get actual range and create bins and levels
start_time = time.time()
min_val, max_val = get_intensity_range(img_masked)
execution_times['get_intensity_range'] = time.time() - start_time

start_time = time.time()
bins, levels = create_bins_levels(min_val, max_val, n_levels=BIN_LEVELS)
execution_times['create_bins_levels'] = time.time() - start_time

# Apply median filter to despeckle
start_time = time.time()
#filtered = median_filter(quantized, size=PIXEL_NEIGHBOR)
gaussian = gaussian_filter(img_masked, SIGMA_GAUSSIAN)
filtered = quantize(gaussian, bins, levels)

execution_times['median_filter'] = time.time() - start_time


# --- Print Execution Times ---
print("--- Function Execution Times ---")
for func_name, duration in execution_times.items():
    print(f"{func_name}: {duration:.6f} seconds")
print("------------------------------")

# --- Show results ---
plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
plt.title('Original Image')
plt.imshow(img, cmap='gray')
plt.axis('off')

plt.subplot(1, 3, 2)
plt.title('Gaussian')
plt.imshow(gaussian, cmap='gray')
plt.axis('off')

plt.subplot(1, 3, 3)
plt.title('Quantized')
plt.imshow(filtered, cmap='gray')
plt.axis('off')

plt.figtext(0.5, 0.01, f'SIGMA_GAUSSIAN: {SIGMA_GAUSSIAN}  BIN_LEVELS: {BIN_LEVELS}', ha='center', fontsize=12)
plt.suptitle('Image Processing Pipeline', fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()