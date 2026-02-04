"""
Add more library scripts to the database
This supplements the initial 3 scripts with the additional 4 from the frontend
"""
import sys
import pathlib

# Add backend to path
sys.path.insert(0, str(pathlib.Path(__file__).parent / "backend"))

from backend.database import get_db_session
from backend.models import LibraryScript

# Additional library scripts to add (extracted from frontend)
ADDITIONAL_SCRIPTS = [
    {
        "name": "Brightness Threshold",
        "description": "Highlights pixels above a brightness threshold. Uses ScriptParameters for the threshold value.",
        "category": "Analysis",
        "tags": ["threshold", "analysis", "parameters"],
        "code": """# MAPS Script Bridge - Brightness Threshold
# Highlights pixels above a configurable threshold

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # Get threshold from script parameters (default: 128)
    try:
        threshold = float(request.ScriptParameters) if request.ScriptParameters else 128
    except ValueError:
        threshold = 128
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    
    MapsBridge.LogInfo(f"Loaded: {input_filename}, Threshold: {threshold}")
    
    # 3. Apply threshold - pixels above threshold become white, below become black
    result = img.point(lambda p: 255 if p > threshold else 0)
    
    # 4. Save to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "threshold_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_threshold.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Threshold " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Highlight", (255, 0, 0), True, outputTileSet.Guid)
    
    # 6. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Highlight", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] threshold={threshold}\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
    },
    {
        "name": "Edge Detection",
        "description": "Detects edges in the image using Sobel operator for feature highlighting.",
        "category": "Analysis",
        "tags": ["edge-detection", "sobel", "analysis"],
        "code": """# MAPS Script Bridge - Edge Detection
# Detects edges using Sobel operator

import os
import tempfile
import MapsBridge
from PIL import Image, ImageFilter
import numpy as np

def sobel_edge_detection(img_array):
    \"\"\"Apply Sobel edge detection\"\"\"
    from scipy import ndimage
    
    # Sobel kernels
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    
    # Apply convolution
    gx = ndimage.convolve(img_array.astype(float), sobel_x)
    gy = ndimage.convolve(img_array.astype(float), sobel_y)
    
    # Compute magnitude
    magnitude = np.sqrt(gx**2 + gy**2)
    
    # Normalize to 0-255
    magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
    return magnitude

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img)
    
    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Apply edge detection
    edges = sobel_edge_detection(img_array)
    result = Image.fromarray(edges, mode="L")
    
    # 4. Save to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "edge_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_edges.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Edges " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Edges", (0, 255, 255), True, outputTileSet.Guid)
    
    # 6. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Edges", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] edge detection\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
    },
    {
        "name": "Particle Categorization",
        "description": "Segments particles, measures shape (area, solidity, circularity), and categorizes as round/irregular/small with color-coded output.",
        "category": "Segmentation",
        "tags": ["segmentation", "particles", "shape-analysis"],
        "code": """# MAPS Script Bridge - Particle Categorization
# Segments particles in EM images, measures shape, and categorizes them.
# Outputs:
#   1) Grayscale mask (labels per particle)
#   2) RGB visualization colored by category (round / irregular / small)

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
from scipy import ndimage
from skimage import filters, morphology, measure, exposure

# ============================================================================
# TUNABLE PARAMETERS - Adjust for your specific images
# ============================================================================

GAUSSIAN_SIGMA = 1.5          # Noise reduction blur
CLAHE_CLIP_LIMIT = 0.03       # Contrast enhancement
MIN_PARTICLE_SIZE = 50        # Minimum particle area in pixels
FILL_HOLES = True             # Fill holes inside particles

# In this image, particles are BRIGHT on a DARK background
PARTICLES_ARE_DARK = False

# ---- Categorization thresholds ---------------------------------------------

# Anything smaller than this (in pixels) is "small"
SMALL_AREA_THRESHOLD = 300

# Circularity = 4*pi*area / perimeter^2
# Perfect circle = 1.0, irregular shapes < 0.8
CIRCULARITY_ROUND_THRESHOLD = 0.8

# Solidity = area / convex_hull_area
# Solid objects close to 1.0, objects with concavities < 0.9
SOLIDITY_ROUND_THRESHOLD = 0.9

# ============================================================================

def preprocess_image(img_array):
    \"\"\"Apply contrast enhancement and noise reduction\"\"\"
    # Apply CLAHE for local contrast
    img_clahe = exposure.equalize_adapthist(img_array, clip_limit=CLAHE_CLIP_LIMIT)
    
    # Gaussian blur to reduce noise
    img_blur = ndimage.gaussian_filter(img_clahe, sigma=GAUSSIAN_SIGMA)
    
    return img_blur

def segment_particles(img_array, particles_are_dark=False):
    \"\"\"Segment particles using Otsu thresholding\"\"\"
    # Otsu threshold
    threshold = filters.threshold_otsu(img_array)
    
    # Create binary mask
    if particles_are_dark:
        binary = img_array < threshold
    else:
        binary = img_array > threshold
    
    # Fill holes if requested
    if FILL_HOLES:
        binary = ndimage.binary_fill_holes(binary)
    
    # Remove small objects
    binary = morphology.remove_small_objects(binary, min_size=MIN_PARTICLE_SIZE)
    
    # Label connected components
    labels = measure.label(binary)
    
    return labels

def categorize_particles(labels):
    \"\"\"Categorize each particle by shape metrics\"\"\"
    props = measure.regionprops(labels)
    
    categories = {}  # particle_label -> category
    
    for prop in props:
        label = prop.label
        area = prop.area
        perimeter = prop.perimeter
        
        # Calculate metrics
        circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
        solidity = prop.solidity
        
        # Categorize
        if area < SMALL_AREA_THRESHOLD:
            categories[label] = 'small'
        elif circularity >= CIRCULARITY_ROUND_THRESHOLD and solidity >= SOLIDITY_ROUND_THRESHOLD:
            categories[label] = 'round'
        else:
            categories[label] = 'irregular'
    
    return categories

def create_category_visualization(labels, categories):
    \"\"\"Create RGB image colored by category\"\"\"
    h, w = labels.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Color mapping
    colors = {
        'small': (100, 100, 100),      # Gray
        'round': (0, 255, 0),           # Green
        'irregular': (255, 165, 0)      # Orange
    }
    
    for label, category in categories.items():
        mask = labels == label
        rgb[mask] = colors[category]
    
    return rgb

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img) / 255.0  # Normalize to 0-1
    
    MapsBridge.LogInfo(f"Loaded: {input_filename}")
    
    # 3. Preprocess
    img_processed = preprocess_image(img_array)
    
    # 4. Segment particles
    labels = segment_particles(img_processed, PARTICLES_ARE_DARK)
    num_particles = labels.max()
    MapsBridge.LogInfo(f"Found {num_particles} particles")
    
    # 5. Categorize particles
    categories = categorize_particles(labels)
    
    # Count categories
    small_count = sum(1 for c in categories.values() if c == 'small')
    round_count = sum(1 for c in categories.values() if c == 'round')
    irregular_count = sum(1 for c in categories.values() if c == 'irregular')
    
    MapsBridge.LogInfo(f"Categories - Small: {small_count}, Round: {round_count}, Irregular: {irregular_count}")
    
    # 6. Create visualizations
    rgb_viz = create_category_visualization(labels, categories)
    
    # 7. Save outputs
    output_folder = os.path.join(tempfile.gettempdir(), "particle_output")
    os.makedirs(output_folder, exist_ok=True)
    base, _ = os.path.splitext(input_filename)
    
    rgb_path = os.path.join(output_folder, f"{base}_categories.png")
    Image.fromarray(rgb_viz).save(rgb_path)
    
    # 8. Create output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Particles " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 9. Create channels
    MapsBridge.CreateChannel("Categories", (255, 255, 255), True, outputTileSet.Guid)
    
    # 10. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Categories", rgb_path, True, outputTileSet.Guid
    )
    
    # 11. Add notes
    notes = f"Tile [{tileInfo.Column}, {tileInfo.Row}]\\n"
    notes += f"Total particles: {num_particles}\\n"
    notes += f"Small (gray): {small_count}\\n"
    notes += f"Round (green): {round_count}\\n"
    notes += f"Irregular (orange): {irregular_count}\\n"
    MapsBridge.AppendNotes(notes, outputTileSet.Guid)
    
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
    },
    {
        "name": "False Color - Single Image",
        "description": "Applies Viridis colormap for single-image visualization (RGB output in one image file).",
        "category": "Visualization",
        "tags": ["colormap", "viridis", "false-color"],
        "code": """# MAPS Script Bridge Example - False Color (Single Image)
# Outputs a single RGB image with Viridis colormap applied

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    gray_array = np.array(img)
    
    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Apply Viridis colormap
    # Normalize to 0-1
    normalized = gray_array.astype(np.float32) / 255.0
    
    # Apply colormap
    cmap = plt.get_cmap('viridis')
    colored = cmap(normalized)
    
    # Convert to RGB (0-255)
    rgb = (colored[:, :, :3] * 255).astype(np.uint8)
    
    # 4. Save output
    output_folder = os.path.join(tempfile.gettempdir(), "viridis_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_viridis.png")
    
    Image.fromarray(rgb).save(output_path)
    
    # 5. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Viridis " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("False Color", (255, 255, 255), True, outputTileSet.Guid)
    
    # 6. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "False Color", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] - Viridis colormap\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
    }
]

def add_scripts():
    print("=" * 60)
    print("Adding More Library Scripts")
    print("=" * 60)
    print()
    
    with get_db_session() as db:
        # Check existing scripts
        existing_names = {s.name for s in db.query(LibraryScript).all()}
        
        added_count = 0
        skipped_count = 0
        
        for script_data in ADDITIONAL_SCRIPTS:
            # Check if script already exists
            if script_data["name"] in existing_names:
                print(f"⤳ Skipping (already exists): {script_data['name']}")
                skipped_count += 1
                continue
            
            # Create new library script
            script = LibraryScript(
                name=script_data["name"],
                filename=script_data["name"].lower().replace(" ", "_").replace("-", "_") + ".py",
                description=script_data["description"],
                code=script_data["code"],
                category=script_data["category"],
                tags=script_data["tags"]
            )
            db.add(script)
            print(f"✓ Added: {script_data['name']}")
            added_count += 1
        
        db.commit()
        
        print()
        print("=" * 60)
        print(f"✓ Added {added_count} new scripts! ({skipped_count} skipped)")
        print("=" * 60)

if __name__ == "__main__":
    add_scripts()
