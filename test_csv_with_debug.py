# Last Code Update - 10:42:19
# MAPS Script Bridge Example - Simple Copy with CSV Output
# Copies input to output (single channel) and adds random CSV data

import os
import tempfile
import MapsBridge
from PIL import Image
import pandas as pd
import numpy as np

def main():
    # 1. Get input
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    
    # Check if there are tiles to process and get the first one
    if not sourceTileSet.Tiles:
        MapsBridge.LogWarning("No tiles found in the source TileSet.")
        return

    # Use ResolveSingleTileAndPath for more robust tile handling
    tile, tileInfo, input_path = MapsBridge.ResolveSingleTileAndPath(request, "0")
    
    if not tile:
        MapsBridge.LogError(f"Could not resolve tile for processing. Request: {request}")
        return
        
    MapsBridge.LogInfo(f"Processing tile [{tile.Column}, {tile.Row}]")

    # 2. Load image
    try:
        img = Image.open(input_path)
    except FileNotFoundError:
        MapsBridge.LogError(f"Input image not found at: {input_path}")
        return
    except Exception as e:
        MapsBridge.LogError(f"Error opening image {input_path}: {e}")
        return

    # 3. Save to temp (no processing)
    output_folder = os.path.join(tempfile.gettempdir(), "copy_output")
    os.makedirs(output_folder, exist_ok=True)
    output_image_path = os.path.join(output_folder, f"tile_{tile.Column}_{tile.Row}.tif")
    
    try:
        img.save(output_image_path)
    except Exception as e:
        MapsBridge.LogError(f"Error saving image to {output_image_path}: {e}")
        return
    
    # 4. Create CSV output with random data
    num_rows = np.random.randint(5, 20) # Random number of rows between 5 and 20
    num_cols = np.random.randint(2, 5)  # Random number of columns between 2 and 5
    
    # Generate random data
    random_data = np.random.rand(num_rows, num_cols)
    
    # Create column names
    column_names = [f"Col_{i+1}" for i in range(num_cols)]
    
    # Create a pandas DataFrame
    df = pd.DataFrame(random_data, columns=column_names)
    
    # Define output path for CSV
    output_csv_path = os.path.join(output_folder, f"tile_{tile.Column}_{tile.Row}_random_data.csv")
    
    try:
        df.to_csv(output_csv_path, index=False)
        MapsBridge.LogInfo(f"Generated random CSV data to {output_csv_path}")
    except Exception as e:
        MapsBridge.LogError(f"Error saving CSV to {output_csv_path}: {e}")
        return

    # 5. Create output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Copy of " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    
    # 6. Create channel for the image output
    image_channel_name = "Copy"
    MapsBridge.CreateChannel(image_channel_name, (255, 255, 255), True, outputTileSetInfo.TileSet.Guid)
    
    # 7. Send image output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        image_channel_name, output_image_path, True, outputTileSetInfo.TileSet.Guid
    )

    # 8. Store the CSV file as a separate output
    MapsBridge.LogInfo(f"About to call StoreFile for: {output_csv_path}")
    MapsBridge.LogInfo(f"CSV file exists: {os.path.exists(output_csv_path)}")
    MapsBridge.LogInfo(f"CSV file size: {os.path.getsize(output_csv_path) if os.path.exists(output_csv_path) else 'N/A'}")
    
    try:
        MapsBridge.StoreFile(
            output_csv_path,
            overwrite=True,
            keepFile=True,
            targetLayerGuid=outputTileSetInfo.TileSet.Guid
        )
        MapsBridge.LogInfo(f"Stored CSV file: {output_csv_path}")
    except Exception as e:
        MapsBridge.LogError(f"Error storing CSV file {output_csv_path}: {e}")
        import traceback
        MapsBridge.LogError(f"Traceback: {traceback.format_exc()}")

    MapsBridge.AppendNotes(f"Image copied without modification. Random CSV data generated for tile [{tile.Column}, {tile.Row}].")

if __name__ == "__main__":
    main()
