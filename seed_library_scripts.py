"""
Seed library scripts from hardcoded defaults into the database
Scripts use MapsBridge v1.1.0 API (snake_case)
"""
import sys
sys.path.insert(0, 'backend')

from backend.database import get_db_session
from backend.models import LibraryScript
from datetime import datetime

# Hardcoded library scripts to seed
LIBRARY_SCRIPTS = [
    {
        "name": "Thermal Colormap",
        "description": "Applies a thermal/hot false-color visualization (black \u2192 red \u2192 yellow \u2192 white) using multi-channel output.",
        "category": "Visualization",
        "tags": ["colormap", "thermal", "false-color"],
        "code": """# MAPS Script Bridge Example - False Color (Multi-Channel)
# Outputs separate R/G/B intensity channels for thermal colormap

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np

def get_thermal_channels(gray_array):
    \"\"\"
    Generate thermal colormap as separate intensity channels.
    Black -> Red -> Yellow -> White
    Returns: (red_intensity, green_intensity, blue_intensity) as uint8 arrays
    \"\"\"
    normalized = gray_array.astype(np.float32) / 255.0
    
    r = np.clip(3.0 * normalized, 0, 1)
    g = np.clip(3.0 * normalized - 1.0, 0, 1)
    b = np.clip(3.0 * normalized - 2.0, 0, 1)
    
    return (
        (r * 255).astype(np.uint8),
        (g * 255).astype(np.uint8),
        (b * 255).astype(np.uint8)
    )

def main():
    # 1. Read tile set request
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)
    
    # 2. Load the input image
    input_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, input_filename)
    img = Image.open(input_path).convert("L")
    gray_array = np.array(img)
    
    MapsBridge.log_info(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Generate thermal colormap channels
    red_intensity, green_intensity, blue_intensity = get_thermal_channels(gray_array)
    
    # 4. Save each channel to temp folder
    output_folder = os.path.join(tempfile.gettempdir(), "thermal_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    
    red_path = os.path.join(output_folder, f"{base}_red.png")
    green_path = os.path.join(output_folder, f"{base}_green.png")
    blue_path = os.path.join(output_folder, f"{base}_blue.png")
    
    Image.fromarray(red_intensity, mode="L").save(red_path)
    Image.fromarray(green_intensity, mode="L").save(green_path)
    Image.fromarray(blue_intensity, mode="L").save(blue_path)
    
    # 5. Create output tile set
    output_info = MapsBridge.get_or_create_output_tile_set(
        "Thermal " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    output_tile_set = output_info.tile_set
    
    # 6. Create channels
    MapsBridge.create_channel("Red", (255, 0, 0), True, output_tile_set.guid)
    MapsBridge.create_channel("Green", (0, 255, 0), True, output_tile_set.guid)
    MapsBridge.create_channel("Blue", (0, 0, 255), True, output_tile_set.guid)
    
    # 7. Send outputs
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Red", red_path, True, output_tile_set.guid
    )
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Green", green_path, True, output_tile_set.guid
    )
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Blue", blue_path, True, output_tile_set.guid
    )
    
    MapsBridge.append_notes("Applied thermal colormap (black->red->yellow->white)")

if __name__ == "__main__":
    main()
"""
    },
    {
        "name": "Copy Original",
        "description": "Simple example that copies the input image to output without modification. Useful as a template.",
        "category": "Basic",
        "tags": ["template", "basic", "example"],
        "code": """# MAPS Script Bridge Example - Simple Copy
# Copies input to output (single channel)

import os
import tempfile
import MapsBridge
from PIL import Image

def main():
    # 1. Read tile set request
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)
    
    # 2. Load image
    input_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, input_filename)
    img = Image.open(input_path)
    
    MapsBridge.log_info(f"Processing: {input_filename}")
    
    # 3. Save to temp (no processing)
    output_folder = os.path.join(tempfile.gettempdir(), "copy_output")
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, input_filename)
    img.save(output_path)
    
    # 4. Create output tile set
    output_info = MapsBridge.get_or_create_output_tile_set(
        "Copy of " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    
    # 5. Send output
    MapsBridge.create_channel("Copy", (255, 255, 255), True, output_info.tile_set.guid)
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Copy", output_path, True, output_info.tile_set.guid
    )
    
    MapsBridge.append_notes("Image copied without modification")

if __name__ == "__main__":
    main()
"""
    },
    {
        "name": "False Color (Viridis)",
        "description": "Applies the Viridis colormap for scientific visualization using matplotlib.",
        "category": "Visualization",
        "tags": ["colormap", "viridis", "scientific"],
        "code": """# MAPS Script Bridge Example - Viridis Colormap
import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

def main():
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)
    
    input_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, input_filename)
    img = Image.open(input_path).convert("L")
    gray_array = np.array(img)
    
    MapsBridge.log_info(f"Applying viridis colormap to {input_filename}")
    
    # Apply viridis colormap
    normalized = gray_array.astype(np.float32) / 255.0
    cmap = plt.get_cmap('viridis')
    colored = cmap(normalized)
    rgb_array = (colored[:, :, :3] * 255).astype(np.uint8)
    
    # Save
    output_folder = os.path.join(tempfile.gettempdir(), "viridis_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_viridis.png")
    
    Image.fromarray(rgb_array, mode="RGB").save(output_path)
    
    # Create output
    output_info = MapsBridge.get_or_create_output_tile_set(
        "Viridis " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    
    MapsBridge.create_channel("Viridis", (255, 255, 255), True, output_info.tile_set.guid)
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Viridis", output_path, True, output_info.tile_set.guid
    )
    
    MapsBridge.append_notes("Applied Viridis colormap")

if __name__ == "__main__":
    main()
"""
    },
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
    # 1. Read tile set request
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)
    
    # Get threshold from script parameters (default: 128)
    try:
        threshold = float(request.script_parameters) if request.script_parameters else 128
    except ValueError:
        threshold = 128
    
    # 2. Load the input image
    input_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, input_filename)
    img = Image.open(input_path).convert("L")
    
    MapsBridge.log_info(f"Loaded: {input_filename}, Threshold: {threshold}")
    
    # 3. Apply threshold
    result = img.point(lambda p: 255 if p > threshold else 0)
    
    # 4. Save to temp folder
    output_folder = os.path.join(tempfile.gettempdir(), "threshold_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_threshold.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    output_info = MapsBridge.get_or_create_output_tile_set(
        "Threshold " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    output_tile_set = output_info.tile_set
    MapsBridge.create_channel("Highlight", (255, 0, 0), True, output_tile_set.guid)
    
    # 6. Send output
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Highlight", output_path, True, output_tile_set.guid
    )
    
    MapsBridge.append_notes(f"Tile [{tile_info.column}, {tile_info.row}] threshold={threshold}\\n", output_tile_set.guid)
    MapsBridge.log_info("Done!")

if __name__ == "__main__":
    main()
"""
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
    
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    
    gx = ndimage.convolve(img_array.astype(float), sobel_x)
    gy = ndimage.convolve(img_array.astype(float), sobel_y)
    
    magnitude = np.sqrt(gx**2 + gy**2)
    magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
    return magnitude

def main():
    # 1. Read tile set request
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)
    
    # 2. Load the input image
    input_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img)
    
    MapsBridge.log_info(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Apply edge detection
    edges = sobel_edge_detection(img_array)
    result = Image.fromarray(edges, mode="L")
    
    # 4. Save to temp folder
    output_folder = os.path.join(tempfile.gettempdir(), "edge_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_edges.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    output_info = MapsBridge.get_or_create_output_tile_set(
        "Edges " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    output_tile_set = output_info.tile_set
    MapsBridge.create_channel("Edges", (0, 255, 255), True, output_tile_set.guid)
    
    # 6. Send output
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Edges", output_path, True, output_tile_set.guid
    )
    
    MapsBridge.append_notes(f"Tile [{tile_info.column}, {tile_info.row}] edge detection\\n", output_tile_set.guid)
    MapsBridge.log_info("Done!")

if __name__ == "__main__":
    main()
"""
    },
    {
        "name": "Particle Categorization",
        "description": "Segments particles, measures shape (area, solidity, circularity), and categorizes as round/irregular/small with color-coded output.",
        "category": "Segmentation",
        "tags": ["segmentation", "particles", "shape-analysis"],
        "code": """# MAPS Script Bridge - Particle Categorization
# Segments particles in EM images, measures shape, and categorizes them.

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
from scipy import ndimage
from skimage import filters, morphology, measure, exposure

# Tunable parameters
GAUSSIAN_SIGMA = 1.5
CLAHE_CLIP_LIMIT = 0.03
MIN_PARTICLE_SIZE = 50
FILL_HOLES = True
PARTICLES_ARE_DARK = False
SMALL_AREA_THRESHOLD = 300
CIRCULARITY_ROUND_THRESHOLD = 0.8
SOLIDITY_ROUND_THRESHOLD = 0.9

def preprocess_image(img_array):
    img_clahe = exposure.equalize_adapthist(img_array, clip_limit=CLAHE_CLIP_LIMIT)
    img_blur = ndimage.gaussian_filter(img_clahe, sigma=GAUSSIAN_SIGMA)
    return img_blur

def segment_particles(img_array, particles_are_dark=False):
    threshold = filters.threshold_otsu(img_array)
    if particles_are_dark:
        binary = img_array < threshold
    else:
        binary = img_array > threshold
    if FILL_HOLES:
        binary = ndimage.binary_fill_holes(binary)
    binary = morphology.remove_small_objects(binary, min_size=MIN_PARTICLE_SIZE)
    labels = measure.label(binary)
    return labels

def categorize_particles(labels):
    props = measure.regionprops(labels)
    categories = {}
    for prop in props:
        label = prop.label
        area = prop.area
        perimeter = prop.perimeter
        circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
        solidity = prop.solidity
        if area < SMALL_AREA_THRESHOLD:
            categories[label] = 'small'
        elif circularity >= CIRCULARITY_ROUND_THRESHOLD and solidity >= SOLIDITY_ROUND_THRESHOLD:
            categories[label] = 'round'
        else:
            categories[label] = 'irregular'
    return categories

def create_category_visualization(labels, categories):
    h, w = labels.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    colors = {
        'small': (100, 100, 100),
        'round': (0, 255, 0),
        'irregular': (255, 165, 0)
    }
    for label, category in categories.items():
        mask = labels == label
        rgb[mask] = colors[category]
    return rgb

def main():
    # 1. Read tile set request
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)
    
    # 2. Load the input image
    input_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img) / 255.0
    
    MapsBridge.log_info(f"Loaded: {input_filename}")
    
    # 3. Preprocess
    img_processed = preprocess_image(img_array)
    
    # 4. Segment particles
    labels = segment_particles(img_processed, PARTICLES_ARE_DARK)
    num_particles = labels.max()
    MapsBridge.log_info(f"Found {num_particles} particles")
    
    # 5. Categorize particles
    categories = categorize_particles(labels)
    small_count = sum(1 for c in categories.values() if c == 'small')
    round_count = sum(1 for c in categories.values() if c == 'round')
    irregular_count = sum(1 for c in categories.values() if c == 'irregular')
    MapsBridge.log_info(f"Categories - Small: {small_count}, Round: {round_count}, Irregular: {irregular_count}")
    
    # 6. Create visualization
    rgb_viz = create_category_visualization(labels, categories)
    
    # 7. Save output
    output_folder = os.path.join(tempfile.gettempdir(), "particle_output")
    os.makedirs(output_folder, exist_ok=True)
    base, _ = os.path.splitext(input_filename)
    rgb_path = os.path.join(output_folder, f"{base}_categories.png")
    Image.fromarray(rgb_viz).save(rgb_path)
    
    # 8. Create output tile set
    output_info = MapsBridge.get_or_create_output_tile_set(
        "Particles " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    output_tile_set = output_info.tile_set
    
    # 9. Create channel and send output
    MapsBridge.create_channel("Categories", (255, 255, 255), True, output_tile_set.guid)
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Categories", rgb_path, True, output_tile_set.guid
    )
    
    # 10. Add notes
    notes = f"Tile [{tile_info.column}, {tile_info.row}]\\n"
    notes += f"Total particles: {num_particles}\\n"
    notes += f"Small (gray): {small_count}\\n"
    notes += f"Round (green): {round_count}\\n"
    notes += f"Irregular (orange): {irregular_count}\\n"
    MapsBridge.append_notes(notes, output_tile_set.guid)
    
    MapsBridge.log_info("Done!")

if __name__ == "__main__":
    main()
"""
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
    # 1. Read tile set request
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)
    
    # 2. Load the input image
    input_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, input_filename)
    img = Image.open(input_path).convert("L")
    gray_array = np.array(img)
    
    MapsBridge.log_info(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Apply Viridis colormap
    normalized = gray_array.astype(np.float32) / 255.0
    cmap = plt.get_cmap('viridis')
    colored = cmap(normalized)
    rgb = (colored[:, :, :3] * 255).astype(np.uint8)
    
    # 4. Save output
    output_folder = os.path.join(tempfile.gettempdir(), "viridis_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_viridis.png")
    Image.fromarray(rgb).save(output_path)
    
    # 5. Create output tile set and channel
    output_info = MapsBridge.get_or_create_output_tile_set(
        "Viridis " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    output_tile_set = output_info.tile_set
    MapsBridge.create_channel("False Color", (255, 255, 255), True, output_tile_set.guid)
    
    # 6. Send output
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "False Color", output_path, True, output_tile_set.guid
    )
    
    MapsBridge.append_notes(f"Tile [{tile_info.column}, {tile_info.row}] - Viridis colormap\\n", output_tile_set.guid)
    MapsBridge.log_info("Done!")

if __name__ == "__main__":
    main()
"""
    }
]


def seed_library_scripts():
    """Seed the library_scripts table with default examples"""
    print("=" * 60)
    print("Seeding Library Scripts (MapsBridge v1.1.0 API)")
    print("=" * 60)
    print()
    
    with get_db_session() as db:
        existing_count = db.query(LibraryScript).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing library scripts")
            response = input("Do you want to replace them? (y/n): ")
            if response.lower() != 'y':
                print("Skipping seed")
                return
            
            db.query(LibraryScript).delete()
            db.commit()
            print(f"Deleted {existing_count} existing scripts")
            print()
        
        added_count = 0
        for script_data in LIBRARY_SCRIPTS:
            library_script = LibraryScript(
                name=script_data["name"],
                filename=f"{script_data['name'].lower().replace(' ', '_')}.py",
                description=script_data["description"],
                category=script_data["category"],
                tags=script_data["tags"],
                code=script_data["code"]
            )
            db.add(library_script)
            added_count += 1
            print(f"  Added: {script_data['name']}")
        
        db.commit()
        
        print()
        print("=" * 60)
        print(f"Seeded {added_count} library scripts successfully!")
        print("=" * 60)


if __name__ == "__main__":
    seed_library_scripts()
