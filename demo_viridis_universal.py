# Universal Image Processing Script - Works with BOTH TileSet and ImageLayer requests
# This script automatically detects the request type and processes accordingly

import os
import sys
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib.cm as cm

def apply_false_color(input_path: str, output_path: str) -> None:
    """
    Loads an image, applies the 'viridis' colormap, and saves the result.
    The output image is a grayscale intensity map suitable for MAPS channels.
    """
    input_filename = os.path.basename(input_path)
   
    # Load the image and convert to a NumPy array
    MapsBridge.LogInfo(f"Loading: {input_path}")
    try:
        img = Image.open(input_path)
        # Ensure image is in a compatible mode for processing
        if img.mode != 'L' and img.mode != 'RGB':
            img = img.convert('L')
        gray_data = np.array(img)
    except FileNotFoundError:
        MapsBridge.LogError(f"Input file not found: {input_path}")
        return
    except Exception as e:
        MapsBridge.LogError(f"Error loading image {input_path}: {e}")
        return

    # Apply the false color map
    MapsBridge.LogInfo("Applying 'viridis' colormap...")
    min_val = gray_data.min()
    max_val = gray_data.max()
   
    if max_val > min_val:
        normalized_data = (gray_data - min_val) / (max_val - min_val)
    else:
        normalized_data = np.zeros_like(gray_data, dtype=float)
        MapsBridge.LogWarning("Input image has uniform pixel values. Result will be a solid color.")
 
    # Apply the 'viridis' colormap
    colored_data = cm.viridis(normalized_data)
    
    # Convert normalized data to grayscale intensity map (0-255)
    intensity_data_uint8 = (normalized_data * 255).astype(np.uint8)
    result_image = Image.fromarray(intensity_data_uint8, 'L')
 
    # Save output
    try:
        result_image.save(output_path)
        MapsBridge.LogInfo(f"Saved processed grayscale intensity map to: {output_path}")
    except Exception as e:
        MapsBridge.LogError(f"Error saving processed image to {output_path}: {e}")

def process_tile_set_request():
    """Process a TileSet request"""
    MapsBridge.LogInfo("Processing TileSet request...")
    
    # Read the tile set request
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    
    MapsBridge.LogInfo(f"Tile set: {sourceTileSet.Name}")
    MapsBridge.LogInfo(f"Size: {sourceTileSet.ColumnCount}x{sourceTileSet.RowCount}")
    MapsBridge.LogInfo(f"Channels: {sourceTileSet.ChannelCount}")
    
    if not sourceTileSet.Tiles:
        MapsBridge.LogWarning("No tiles found in the tile set.")
        return
    
    # Process first tile
    tileInfo = sourceTileSet.Tiles[0]
    MapsBridge.LogInfo(f"Processing tile [{tileInfo.Column}, {tileInfo.Row}]")
    
    # Get input image filename for channel 0
    input_filename_ch0 = tileInfo.ImageFileNames.get("0")
    if not input_filename_ch0:
        MapsBridge.LogError(f"No image file found for channel '0'")
        return
    
    input_path = os.path.join(sourceTileSet.DataFolderPath, input_filename_ch0)
    
    # Define output path
    output_folder_temp = os.path.join(tempfile.gettempdir(), "processed_tile_output")
    os.makedirs(output_folder_temp, exist_ok=True)
    base, ext = os.path.splitext(input_filename_ch0)
    processed_output_path = os.path.join(output_folder_temp, f"{base}_viridis.png")
    
    # Process the image
    apply_false_color(input_path, processed_output_path)
    
    # Create output tile set
    output_tile_set_name = "Viridis Results for " + sourceTileSet.Name
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        output_tile_set_name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # Create channel
    channel_name = "Viridis Intensity"
    MapsBridge.CreateChannel(channel_name, (255, 255, 255), True, outputTileSet.Guid)
    
    # Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        channel_name, processed_output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(
        f"Processed tile [{tileInfo.Column}, {tileInfo.Row}] using viridis colormap.\n",
        outputTileSet.Guid
    )
    
    MapsBridge.LogInfo("TileSet processing completed!")

def process_image_layer_request():
    """Process an ImageLayer request"""
    MapsBridge.LogInfo("Processing ImageLayer request...")
    
    # Read the image layer request
    request = MapsBridge.ScriptImageLayerRequest.FromStdIn()
    sourceImageLayer = request.SourceImageLayer
    
    MapsBridge.LogInfo(f"Image layer: {sourceImageLayer.Name}")
    MapsBridge.LogInfo(f"Resolution: {sourceImageLayer.TotalLayerResolution.Width}x{sourceImageLayer.TotalLayerResolution.Height}")
    MapsBridge.LogInfo(f"Channels: {sourceImageLayer.ChannelCount}")
    
    if not request.PreparedImages:
        MapsBridge.LogWarning("No prepared images found.")
        return
    
    # Get first prepared image (channel 0)
    input_path = request.PreparedImages.get("0")
    if not input_path:
        MapsBridge.LogError("No image file found for channel '0'")
        return
    
    MapsBridge.LogInfo(f"Input image: {input_path}")
    
    # Define output path
    output_folder_temp = os.path.join(tempfile.gettempdir(), "processed_layer_output")
    os.makedirs(output_folder_temp, exist_ok=True)
    input_filename = os.path.basename(input_path)
    base, ext = os.path.splitext(input_filename)
    processed_output_path = os.path.join(output_folder_temp, f"{base}_viridis.png")
    
    # Process the image
    apply_false_color(input_path, processed_output_path)
    
    # Create image layer with the processed result
    output_layer_name = "Viridis " + sourceImageLayer.Name
    MapsBridge.CreateImageLayer(
        output_layer_name,
        processed_output_path,
        targetLayerGroupName="Outputs",
        keepFile=True
    )
    
    MapsBridge.LogInfo(f"Created image layer: {output_layer_name}")
    MapsBridge.LogInfo("ImageLayer processing completed!")

def main():
    try:
        # Read the JSON from stdin once
        MapsBridge.LogInfo("Reading request from stdin...")
        json_input = sys.stdin.readline().strip()
        
        if not json_input:
            MapsBridge.LogError("No input received from stdin")
            sys.exit(1)
        
        # Parse to get RequestType
        import json
        data = json.loads(json_input)
        request_type = data.get("RequestType", "TileSetRequest")
        
        MapsBridge.LogInfo(f"Request type: {request_type}")
        
        # Parse the appropriate request type using FromJson
        if request_type == "ImageLayerRequest":
            request = MapsBridge.ScriptImageLayerRequest.FromJson(json_input)
            sourceImageLayer = request.SourceImageLayer
            
            MapsBridge.LogInfo(f"Image layer: {sourceImageLayer.Name}")
            MapsBridge.LogInfo(f"Resolution: {sourceImageLayer.TotalLayerResolution.Width}x{sourceImageLayer.TotalLayerResolution.Height}")
            
            if not request.PreparedImages:
                MapsBridge.LogWarning("No prepared images found.")
                return
            
            # Get first prepared image (channel 0)
            input_path = request.PreparedImages.get("0")
            if not input_path:
                MapsBridge.LogError("No image file found for channel '0'")
                return
            
            # Process the image
            output_folder_temp = os.path.join(tempfile.gettempdir(), "processed_layer_output")
            os.makedirs(output_folder_temp, exist_ok=True)
            input_filename = os.path.basename(input_path)
            base, ext = os.path.splitext(input_filename)
            processed_output_path = os.path.join(output_folder_temp, f"{base}_viridis.png")
            
            apply_false_color(input_path, processed_output_path)
            
            # Create image layer with the processed result
            output_layer_name = "Viridis " + sourceImageLayer.Name
            MapsBridge.CreateImageLayer(
                output_layer_name,
                processed_output_path,
                targetLayerGroupName="Outputs",
                keepFile=True
            )
            
            MapsBridge.LogInfo("ImageLayer processing completed!")
            
        else:  # TileSetRequest
            request = MapsBridge.ScriptTileSetRequest.FromJson(json_input)
            sourceTileSet = request.SourceTileSet
            
            MapsBridge.LogInfo(f"Tile set: {sourceTileSet.Name}")
            MapsBridge.LogInfo(f"Size: {sourceTileSet.ColumnCount}x{sourceTileSet.RowCount}")
            
            if not sourceTileSet.Tiles:
                MapsBridge.LogWarning("No tiles found.")
                return
            
            # Process first tile
            tileInfo = sourceTileSet.Tiles[0]
            input_filename = tileInfo.ImageFileNames.get("0")
            if not input_filename:
                MapsBridge.LogError("No image file found for channel '0'")
                return
            
            input_path = os.path.join(sourceTileSet.DataFolderPath, input_filename)
            
            # Process the image
            output_folder_temp = os.path.join(tempfile.gettempdir(), "processed_tile_output")
            os.makedirs(output_folder_temp, exist_ok=True)
            base, ext = os.path.splitext(input_filename)
            processed_output_path = os.path.join(output_folder_temp, f"{base}_viridis.png")
            
            apply_false_color(input_path, processed_output_path)
            
            # Create output tile set
            output_tile_set_name = "Viridis Results"
            outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
                output_tile_set_name,
                targetLayerGroupName="Outputs"
            )
            outputTileSet = outputTileSetInfo.TileSet
            
            # Create channel and send output
            channel_name = "Viridis"
            MapsBridge.CreateChannel(channel_name, (255, 255, 255), True, outputTileSet.Guid)
            MapsBridge.SendSingleTileOutput(
                tileInfo.Row, tileInfo.Column,
                channel_name, processed_output_path, True, outputTileSet.Guid
            )
            
            MapsBridge.LogInfo("TileSet processing completed!")
            
    except Exception as e:
        MapsBridge.LogError(f"Script error: {e}")
        import traceback
        MapsBridge.LogError(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
