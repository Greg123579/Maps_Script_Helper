"""
Seed library scripts from hardcoded defaults into the database
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
        "description": "Applies a thermal/hot false-color visualization (black → red → yellow → white) using multi-channel output.",
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
    
    # Each channel is a grayscale intensity map
    r = np.clip(3.0 * normalized, 0, 1)
    g = np.clip(3.0 * normalized - 1.0, 0, 1)
    b = np.clip(3.0 * normalized - 2.0, 0, 1)
    
    return (
        (r * 255).astype(np.uint8),
        (g * 255).astype(np.uint8),
        (b * 255).astype(np.uint8)
    )

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
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Thermal " + sourceTileSet.Name, 
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 6. Create channels
    MapsBridge.CreateChannel("Red", (255, 0, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Green", (0, 255, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Blue", (0, 0, 255), True, outputTileSet.Guid)
    
    # 7. Send outputs
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Red", red_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Green", green_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Blue", blue_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes("Applied thermal colormap (black->red->yellow->white)")

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
    # 1. Get input
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load image
    input_filename = tileInfo.ImageFileNames["0"]
    input_path = os.path.join(sourceTileSet.DataFolderPath, input_filename)
    img = Image.open(input_path)
    
    MapsBridge.LogInfo(f"Processing: {input_filename}")
    
    # 3. Save to temp (no processing)
    output_folder = os.path.join(tempfile.gettempdir(), "copy_output")
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, input_filename)
    img.save(output_path)
    
    # 4. Create output
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Copy of " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    
    # 5. Send output
    MapsBridge.CreateChannel("Copy", (255, 255, 255), True, outputTileSetInfo.TileSet.Guid)
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Copy", output_path, True, outputTileSetInfo.TileSet.Guid
    )
    
    MapsBridge.AppendNotes("Image copied without modification")

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
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    input_filename = tileInfo.ImageFileNames["0"]
    input_path = os.path.join(sourceTileSet.DataFolderPath, input_filename)
    img = Image.open(input_path).convert("L")
    gray_array = np.array(img)
    
    MapsBridge.LogInfo(f"Applying viridis colormap to {input_filename}")
    
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
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Viridis " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    
    MapsBridge.CreateChannel("Viridis", (255, 255, 255), True, outputTileSetInfo.TileSet.Guid)
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Viridis", output_path, True, outputTileSetInfo.TileSet.Guid
    )
    
    MapsBridge.AppendNotes("Applied Viridis colormap")

if __name__ == "__main__":
    main()
"""
    }
]


def seed_library_scripts():
    """Seed the library_scripts table with default examples"""
    print("=" * 60)
    print("Seeding Library Scripts")
    print("=" * 60)
    print()
    
    with get_db_session() as db:
        # Check if scripts already exist
        existing_count = db.query(LibraryScript).count()
        if existing_count > 0:
            print(f"⚠ Found {existing_count} existing library scripts")
            response = input("Do you want to replace them? (y/n): ")
            if response.lower() != 'y':
                print("Skipping seed")
                return
            
            # Delete existing
            db.query(LibraryScript).delete()
            db.commit()
            print(f"✓ Deleted {existing_count} existing scripts")
            print()
        
        # Add library scripts
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
            print(f"✓ Added: {script_data['name']}")
        
        db.commit()
        
        print()
        print("=" * 60)
        print(f"✓ Seeded {added_count} library scripts successfully!")
        print("=" * 60)


if __name__ == "__main__":
    seed_library_scripts()
