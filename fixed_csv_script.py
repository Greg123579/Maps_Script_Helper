# Last Code Update - Fixed CSV Output
# MAPS Script Bridge Example - Simple Copy with CSV Output
# Copies input to output (single channel) and adds a random CSV

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
    
    # Process only the first tile for this example
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load image
    input_filename = tileInfo.ImageFileNames["0"]
    input_path = os.path.join(sourceTileSet.DataFolderPath, input_filename)
    try:
        img = Image.open(input_path)
    except FileNotFoundError:
        MapsBridge.LogError(f"Image file not found at: {input_path}")
        return
    except Exception as e:
        MapsBridge.LogError(f"Error opening image file: {e}")
        return

    MapsBridge.LogInfo(f"Processing: {input_filename}")
    
    # 3. Save image to temp
    output_folder = os.path.join(tempfile.gettempdir(), "copy_output")
    os.makedirs(output_folder, exist_ok=True)
    image_output_path = os.path.join(output_folder, input_filename)
    try:
        img.save(image_output_path)
    except Exception as e:
        MapsBridge.LogError(f"Error saving image file: {e}")
        return
    
    # --- CSV Output Section ---
    
    # Generate random data for CSV
    num_rows = np.random.randint(5, 15) # Random number of rows between 5 and 14
    num_cols = np.random.randint(2, 5)  # Random number of columns between 2 and 4
    
    # Create random data with string column names
    data = np.random.rand(num_rows, num_cols)
    column_names = [f"Random_Col_{i+1}" for i in range(num_cols)]
    df = pd.DataFrame(data, columns=column_names)
    
    # Save CSV to temp folder (works in both MAPS and Helper App)
    csv_output_path = os.path.join(output_folder, f"random_data_{tileInfo.Column}_{tileInfo.Row}.csv")
    
    # Save DataFrame to CSV
    try:
        df.to_csv(csv_output_path, index=False)
        MapsBridge.LogInfo(f"Generated CSV: {csv_output_path}")
    except Exception as e:
        MapsBridge.LogError(f"Error saving CSV file: {e}")
        return
    
    # --- End CSV Output Section ---

    # 4. Create output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Copy of " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    
    # 5. Send image output
    MapsBridge.CreateChannel("Copy", (255, 255, 255), True, outputTileSetInfo.TileSet.Guid)
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Copy", image_output_path, True, outputTileSetInfo.TileSet.Guid
    )
    
    # Store the CSV file as an output (works in both MAPS and Helper App)
    try:
        MapsBridge.StoreFile(
            csv_output_path,
            overwrite=True,
            keepFile=True,
            targetLayerGuid=outputTileSetInfo.TileSet.Guid
        )
        MapsBridge.LogInfo(f"Stored CSV file: {os.path.basename(csv_output_path)}")
    except Exception as e:
        MapsBridge.LogError(f"Error storing CSV file: {e}")

    MapsBridge.AppendNotes("Image copied without modification. Random CSV data generated.")

if __name__ == "__main__":
    main()
