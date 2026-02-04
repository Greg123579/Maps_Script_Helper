"""
MapsBridge.py - Shim module for MAPS Script Bridge compatibility

This module provides a compatible API with the real MAPS Script Bridge (MapsBridge)
used in Thermo Fisher's MAPS software. It allows scripts written for MAPS to run
in the helper app environment without modification.

In the real MAPS environment:
- ScriptTileSetRequest.FromStdIn() reads JSON from stdin
- SendSingleTileOutput() sends JSON back to MAPS via stdout

In this helper environment:
- ScriptTileSetRequest.FromStdIn() scans /input for images and builds a fake request
- SendSingleTileOutput() copies output images to /output for the UI to display
"""

import os
import sys
import shutil
import uuid
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Iterable
from dataclasses import dataclass, field

# Try to import PIL for image metadata extraction
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Debug flag - set to True for verbose logging
DEBUG = True

def _debug(msg: str) -> None:
    """Print debug message if DEBUG is enabled"""
    if DEBUG:
        print(f"[MapsBridge DEBUG] {msg}")


# ============================================================================
# Data Classes - Match real MapsBridge interface exactly
# ============================================================================

@dataclass
class PointInt:
    """Integer point (X, Y)"""
    X: int
    Y: int

@dataclass
class PointFloat:
    """Float point (X, Y)"""
    X: float
    Y: float

@dataclass
class SizeInt:
    """Integer size (Width, Height)"""
    Width: int
    Height: int

@dataclass
class SizeFloat:
    """Float size (Width, Height)"""
    Width: float
    Height: float

@dataclass
class Tile:
    """Simple tile reference with column and row"""
    Column: int
    Row: int

@dataclass
class TileInfo:
    """Detailed information about a single tile"""
    Column: int
    Row: int
    StagePosition: PointFloat
    TileCenterPixelOffset: PointInt
    ImageFileNames: Dict[str, str]  # Channel index (as string) -> filename

@dataclass
class ChannelInfo:
    """Channel information"""
    Index: int
    Name: str
    Color: str

@dataclass
class TileSetInfo:
    """Complete tile set information"""
    Guid: str
    Name: str
    DataFolderPath: str
    ColumnCount: int
    RowCount: int
    ChannelCount: int
    IsCompleted: bool
    Size: SizeFloat
    TileSize: SizeFloat
    TileResolution: SizeInt
    PixelFormat: str
    StagePosition: PointFloat
    Rotation: float
    PixelToStageMatrix: List[List[float]]
    AcquisitionStagePosition: PointFloat
    AcquisitionStageRotation: float
    AcquisitionRotation: float
    Channels: List[ChannelInfo]
    Tiles: List[TileInfo]

@dataclass
class ImageLayerInfo:
    """Image layer information"""
    Guid: str
    Name: str
    StagePosition: PointFloat
    Rotation: float
    DataFolderPath: str
    Size: SizeFloat
    TotalLayerResolution: SizeInt
    PixelToStageMatrix: List[List[float]]
    ChannelCount: int
    Channels: List[ChannelInfo]
    OriginalTileSet: Optional[TileSetInfo] = None

@dataclass
class ScriptTileSetRequest:
    """
    Tile set processing request from MAPS.
    
    In the real MAPS environment, this is populated from JSON via stdin.
    In the helper environment, FromStdIn() builds a fake request from /input files.
    """
    RequestType: str
    SourceTileSet: TileSetInfo
    ScriptName: str
    ScriptParameters: str
    TilesToProcess: List[Tile]
    
    @staticmethod
    def FromStdIn() -> "ScriptTileSetRequest":
        """
        Build a ScriptTileSetRequest from the environment.
        
        In real MAPS: reads JSON from stdin
        In helper app: scans /input for images and builds a fake request
        """
        _debug("ScriptTileSetRequest.FromStdIn() called")
        # Use INPUT_DIR environment variable if set, otherwise default to /input
        input_dir_str = os.environ.get('INPUT_DIR', '/input')
        input_dir = Path(input_dir_str)
        _debug(f"Input directory: {input_dir}, exists: {input_dir.exists()}")
        
        # Find all image files in /input
        image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.bmp", "*.gif"]
        image_files = []
        for ext in image_extensions:
            found = list(input_dir.glob(ext))
            found_upper = list(input_dir.glob(ext.upper()))
            image_files.extend(found)
            image_files.extend(found_upper)
        
        # If no standard image files found, include ALL files
        if not image_files:
            _debug("  No standard image extensions found, checking all files...")
            all_files = [f for f in input_dir.iterdir() if f.is_file()]
            excluded = {'.gitkeep', '.ds_store', 'thumbs.db', '.matplotlib'}
            image_files = [f for f in all_files if f.name.lower() not in excluded and not f.name.startswith('.')]
        
        image_files = sorted(set(image_files))
        _debug(f"Total image files found: {len(image_files)}")
        
        # Get script parameters from environment variable if set
        script_params = os.environ.get("MAPS_SCRIPT_PARAMETERS", "")
        
        # Extract image metadata
        tile_pixel_width = 1024
        tile_pixel_height = 1024
        pixel_format = "Gray8"
        
        if image_files and HAS_PIL:
            try:
                first_image = Image.open(image_files[0])
                tile_pixel_width, tile_pixel_height = first_image.size
                if first_image.mode == 'L':
                    pixel_format = "Gray8"
                elif first_image.mode == 'I;16':
                    pixel_format = "Gray16"
                elif first_image.mode == 'RGB':
                    pixel_format = "Bgr24"
                elif first_image.mode == 'RGBA':
                    pixel_format = "Bgra32"
                _debug(f"Extracted image metadata: {tile_pixel_width}x{tile_pixel_height}, format={pixel_format}")
            except Exception as e:
                _debug(f"Failed to extract image metadata: {e}")
        
        # Calculate realistic field of view (assume 10 nm per pixel)
        pixel_size_meters = 10e-9  # 10 nm per pixel
        tile_width_meters = tile_pixel_width * pixel_size_meters
        tile_height_meters = tile_pixel_height * pixel_size_meters
        
        # Build channel info
        default_channel = ChannelInfo(Index=0, Name="Default", Color="#FFFFFF")
        
        # Build tiles
        tiles = []
        if image_files:
            # Create ImageFileNames dict with STRING keys
            image_file_names = {}
            for idx, img_path in enumerate(image_files):
                image_file_names[str(idx)] = img_path.name
            
            tile_info = TileInfo(
                Column=1,
                Row=1,
                StagePosition=PointFloat(X=0.0, Y=0.0),
                TileCenterPixelOffset=PointInt(X=0, Y=0),
                ImageFileNames=image_file_names
            )
            tiles.append(tile_info)
        
        # Build PixelToStageMatrix (identity-like matrix for helper app)
        pixel_to_stage_matrix = [
            [pixel_size_meters, 0, 0],
            [0, pixel_size_meters, 0],
            [0, 0, 1]
        ]
        
        # Build source tile set
        source_tile_set = TileSetInfo(
            Guid="{" + str(uuid.uuid4()).upper() + "}",
            Name="LocalTestTileSet",
            DataFolderPath=str(input_dir),
            ColumnCount=1,
            RowCount=1,
            ChannelCount=1,
            IsCompleted=True,
            Size=SizeFloat(Width=tile_width_meters, Height=tile_height_meters),
            TileSize=SizeFloat(Width=tile_width_meters, Height=tile_height_meters),
            TileResolution=SizeInt(Width=tile_pixel_width, Height=tile_pixel_height),
            PixelFormat=pixel_format,
            StagePosition=PointFloat(X=0.0, Y=0.0),
            Rotation=0.0,
            PixelToStageMatrix=pixel_to_stage_matrix,
            AcquisitionStagePosition=PointFloat(X=0.0, Y=0.0),
            AcquisitionStageRotation=0.0,
            AcquisitionRotation=0.0,
            Channels=[default_channel],
            Tiles=tiles
        )
        
        # For single tile mode, TilesToProcess contains one tile
        tiles_to_process = [Tile(Column=1, Row=1)] if tiles else []
        
        request = ScriptTileSetRequest(
            RequestType="TileSetRequest",
            SourceTileSet=source_tile_set,
            ScriptName="local_test",
            ScriptParameters=script_params,
            TilesToProcess=tiles_to_process
        )
        
        _debug(f"Created ScriptTileSetRequest with {len(tiles)} tiles")
        return request

@dataclass
class ScriptImageLayerRequest:
    """
    Image layer processing request from MAPS.
    """
    RequestType: str
    SourceImageLayer: ImageLayerInfo
    ScriptName: str
    ScriptParameters: str
    PreparedImages: Dict[str, str]  # Channel index (as string) -> full path
    
    @staticmethod
    def FromStdIn() -> "ScriptImageLayerRequest":
        """
        Build a ScriptImageLayerRequest from the environment.
        
        In real MAPS: reads JSON from stdin
        In helper app: scans /input for images and builds a fake request
        """
        _debug("ScriptImageLayerRequest.FromStdIn() called")
        # Use INPUT_DIR environment variable if set, otherwise default to /input
        input_dir_str = os.environ.get('INPUT_DIR', '/input')
        input_dir = Path(input_dir_str)
        _debug(f"Input directory: {input_dir}, exists: {input_dir.exists()}")
        
        # Find all image files in /input
        image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.bmp", "*.gif"]
        image_files = []
        for ext in image_extensions:
            found = list(input_dir.glob(ext))
            found_upper = list(input_dir.glob(ext.upper()))
            image_files.extend(found)
            image_files.extend(found_upper)
        
        # If no standard image files found, include ALL files
        if not image_files:
            _debug("  No standard image extensions found, checking all files...")
            all_files = [f for f in input_dir.iterdir() if f.is_file()]
            excluded = {'.gitkeep', '.ds_store', 'thumbs.db', '.matplotlib'}
            image_files = [f for f in all_files if f.name.lower() not in excluded and not f.name.startswith('.')]
        
        image_files = sorted(set(image_files))
        _debug(f"Total image files found: {len(image_files)}")
        
        # Get script parameters from environment variable if set
        script_params = os.environ.get("MAPS_SCRIPT_PARAMETERS", "")
        
        # Extract image metadata from first image
        layer_pixel_width = 1024
        layer_pixel_height = 1024
        
        if image_files and HAS_PIL:
            try:
                first_image = Image.open(image_files[0])
                layer_pixel_width, layer_pixel_height = first_image.size
                _debug(f"Extracted image metadata: {layer_pixel_width}x{layer_pixel_height}")
            except Exception as e:
                _debug(f"Failed to extract image metadata: {e}")
        
        # Calculate realistic field of view (assume 10 nm per pixel)
        pixel_size_meters = 10e-9  # 10 nm per pixel
        layer_width_meters = layer_pixel_width * pixel_size_meters
        layer_height_meters = layer_pixel_height * pixel_size_meters
        
        # Build channel info (assume all images are different channels)
        channels = []
        for idx in range(len(image_files)):
            channel = ChannelInfo(Index=idx, Name=f"Channel_{idx}", Color="#FFFFFF")
            channels.append(channel)
        
        if not channels:
            # At least create one default channel
            channels.append(ChannelInfo(Index=0, Name="Default", Color="#FFFFFF"))
        
        # Build PreparedImages dict: channel index (as string) -> full path
        prepared_images = {}
        for idx, img_path in enumerate(image_files):
            prepared_images[str(idx)] = str(img_path.resolve())
        
        # Build PixelToStageMatrix (identity-like matrix for helper app)
        pixel_to_stage_matrix = [
            [pixel_size_meters, 0, 0],
            [0, pixel_size_meters, 0],
            [0, 0, 1]
        ]
        
        # Build source image layer
        source_image_layer = ImageLayerInfo(
            Guid="{" + str(uuid.uuid4()).upper() + "}",
            Name="LocalTestImageLayer",
            StagePosition=PointFloat(X=0.0, Y=0.0),
            Rotation=0.0,
            DataFolderPath=str(input_dir),
            Size=SizeFloat(Width=layer_width_meters, Height=layer_height_meters),
            TotalLayerResolution=SizeInt(Width=layer_pixel_width, Height=layer_pixel_height),
            PixelToStageMatrix=pixel_to_stage_matrix,
            ChannelCount=len(channels),
            Channels=channels,
            OriginalTileSet=None
        )
        
        request = ScriptImageLayerRequest(
            RequestType="ImageLayerRequest",
            SourceImageLayer=source_image_layer,
            ScriptName="local_test",
            ScriptParameters=script_params,
            PreparedImages=prepared_images
        )
        
        _debug(f"Created ScriptImageLayerRequest with {len(prepared_images)} prepared images")
        return request


# ============================================================================
# Output Tile Set Management
# ============================================================================

@dataclass
class TileSetCreateInfo:
    """Response info for tile set creation"""
    IsSuccess: bool
    ErrorMessage: str
    IsCreated: bool
    TileSet: Optional[TileSetInfo]

# Global registry for created tile sets and channels
_tile_sets: Dict[str, Dict[str, Any]] = {}
_channels: Dict[str, List[Dict[str, Any]]] = {}
_notes: Dict[str, List[str]] = {}


def GetOrCreateOutputTileSet(
    tileSetName: Optional[str] = None,
    tileResolution: Optional[Tuple[int, int]] = None,
    targetLayerGroupName: Optional[str] = None
) -> TileSetCreateInfo:
    """
    Get or create an output tile set.
    
    In real MAPS: Creates a tile set in the MAPS project via JSON
    In helper app: Returns a TileSetCreateInfo object with a GUID
    """
    # Check if we already have this tile set
    for guid_str, info in _tile_sets.items():
        if info.get("name") == tileSetName:
            _debug(f"Found existing tile set: {tileSetName}")
            return TileSetCreateInfo(
                IsSuccess=True,
                ErrorMessage="",
                IsCreated=False,
                TileSet=info.get("tileset_info")
            )
    
    # Create new tile set
    new_guid = "{" + str(uuid.uuid4()).upper() + "}"
    
    # Build a minimal TileSetInfo for the output
    tile_set_info = TileSetInfo(
        Guid=new_guid,
        Name=tileSetName or "OutputTileSet",
        DataFolderPath="/output",
        ColumnCount=1,
        RowCount=1,
        ChannelCount=0,
        IsCompleted=False,
        Size=SizeFloat(Width=0.001, Height=0.001),
        TileSize=SizeFloat(Width=0.001, Height=0.001),
        TileResolution=SizeInt(Width=tileResolution[0] if tileResolution else 1024, 
                               Height=tileResolution[1] if tileResolution else 1024),
        PixelFormat="Gray8",
        StagePosition=PointFloat(X=0.0, Y=0.0),
        Rotation=0.0,
        PixelToStageMatrix=[[1e-9, 0, 0], [0, 1e-9, 0], [0, 0, 1]],
        AcquisitionStagePosition=PointFloat(X=0.0, Y=0.0),
        AcquisitionStageRotation=0.0,
        AcquisitionRotation=0.0,
        Channels=[],
        Tiles=[]
    )
    
    _tile_sets[new_guid] = {
        "name": tileSetName,
        "layer_group": targetLayerGroupName,
        "resolution": tileResolution,
        "tileset_info": tile_set_info
    }
    
    LogInfo(f"Created output tile set: {tileSetName} (Guid: {new_guid})")
    return TileSetCreateInfo(
        IsSuccess=True,
        ErrorMessage="",
        IsCreated=True,
        TileSet=tile_set_info
    )


def CreateTileSet(
    tileSetName: str,
    stagePosition: Tuple[str, str, str],
    totalSize: Tuple[str, str],
    rotation: Optional[str] = None,
    templateName: Optional[str] = None,
    tileResolution: Optional[Tuple[int, int]] = None,
    tileHfw: Optional[str] = None,
    pixelSize: Optional[str] = None,
    scheduleAcquisition: Optional[bool] = None,
    targetLayerGroupName: Optional[str] = None
) -> TileSetCreateInfo:
    """
    Create a new tile set and prepare it for acquisition.
    
    In real MAPS: Creates tile set and optionally schedules acquisition
    In helper app: Returns a TileSetCreateInfo (stub)
    """
    LogInfo(f"CreateTileSet called: {tileSetName} at {stagePosition}, size {totalSize}")
    return GetOrCreateOutputTileSet(tileSetName, tileResolution, targetLayerGroupName)


# ============================================================================
# Channel Management
# ============================================================================

def CreateChannel(
    channelName: str,
    channelColor: Optional[Tuple[int, int, int]] = (255, 255, 255),
    isAdditive: Optional[bool] = False,
    targetTileSetGuid: Optional[str] = None
) -> None:
    """
    Create a channel in a tile set.
    
    In real MAPS: Sends JSON to create channel
    In helper app: Logs the channel creation (no-op)
    """
    guid = targetTileSetGuid if targetTileSetGuid else "default"
    
    if guid not in _channels:
        _channels[guid] = []
    
    _channels[guid].append({
        "name": channelName,
        "color": channelColor,
        "additive": isAdditive
    })
    
    LogInfo(f"Created channel: {channelName} with color {channelColor}")


# ============================================================================
# Output Functions
# ============================================================================

def SendSingleTileOutput(
    tileRow: int,
    tileColumn: int,
    targetChannelName: str,
    imageFilePath: str,
    keepFile: Optional[bool] = False,
    targetTileSetGuid: Optional[str] = None
) -> None:
    """
    Send a single tile output to MAPS.
    
    In real MAPS: Sends JSON to MAPS via stdout
    In helper app: Copies the image to /output for the UI to display
    """
    _debug(f"SendSingleTileOutput() called:")
    _debug(f"  tileRow={tileRow}, tileColumn={tileColumn}")
    _debug(f"  targetChannelName='{targetChannelName}'")
    _debug(f"  imageFilePath='{imageFilePath}'")
    
    source_path = Path(imageFilePath)
    # Use OUTPUT_DIR environment variable if set, otherwise default to /output
    output_dir_str = os.environ.get('OUTPUT_DIR', '/output')
    output_dir = Path(output_dir_str)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not source_path.exists():
        LogError(f"Output image not found: {imageFilePath}")
        return
    
    # Check if the file is already in /output
    try:
        source_resolved = source_path.resolve()
        output_resolved = output_dir.resolve()
        
        if source_resolved.parent == output_resolved:
            LogInfo(f"Output already in /output: {source_path.name} (Channel: {targetChannelName}, Tile: [{tileColumn}, {tileRow}])")
            return
    except Exception as e:
        _debug(f"  Exception during path resolution: {e}")
        pass
    
    # Build output filename
    original_name = source_path.name
    ext = source_path.suffix
    safe_channel = "".join(c if c.isalnum() or c in "_-" else "_" for c in targetChannelName)
    output_filename = f"{safe_channel}_{original_name}"
    output_path = output_dir / output_filename
    
    # Handle duplicate filenames
    counter = 1
    while output_path.exists():
        base_name = source_path.stem
        output_filename = f"{safe_channel}_{base_name}_{counter}{ext}"
        output_path = output_dir / output_filename
        counter += 1
    
    try:
        shutil.copy2(str(source_path), str(output_path))
        LogInfo(f"Output saved: {output_path.name} (Channel: {targetChannelName}, Tile: [{tileColumn}, {tileRow}])")
    except Exception as e:
        LogError(f"Failed to copy output file: {e}")


def StoreFile(
    filePath: str,
    overwrite: Optional[bool] = False,
    keepFile: Optional[bool] = True,
    targetLayerGuid: Optional[str] = None
) -> None:
    """
    Store a file in the MAPS project.
    
    In real MAPS: Sends JSON to store file
    In helper app: Copies the file to /output
    """
    _debug(f"StoreFile() called:")
    _debug(f"  filePath='{filePath}'")
    _debug(f"  overwrite={overwrite}, keepFile={keepFile}")
    _debug(f"  targetLayerGuid={targetLayerGuid}")
    
    source_path = Path(filePath)
    # Use OUTPUT_DIR environment variable if set, otherwise default to /output
    output_dir_str = os.environ.get('OUTPUT_DIR', '/output')
    output_dir = Path(output_dir_str)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not source_path.exists():
        LogError(f"StoreFile: Source file does not exist: {filePath}")
        _debug(f"  Source path does not exist: {source_path}")
        return
    
    _debug(f"  Source exists: {source_path}")
    _debug(f"  Source absolute path: {source_path.resolve()}")
    
    # Check if already in /output
    try:
        source_resolved = source_path.resolve()
        output_resolved = output_dir.resolve()
        if source_resolved.parent == output_resolved:
            LogInfo(f"File already in /output: {source_path.name}")
            _debug(f"  File already in output directory, skipping copy")
            return
    except Exception as e:
        _debug(f"  Exception checking if file in /output: {e}")
        pass
    
    output_path = output_dir / source_path.name
    _debug(f"  Target output path: {output_path}")
    
    if output_path.exists() and not overwrite:
        LogWarning(f"File already exists and overwrite=False: {output_path.name}")
        _debug(f"  File exists and overwrite=False, skipping")
        return
    
    try:
        shutil.copy2(str(source_path), str(output_path))
        LogInfo(f"File stored: {output_path.name}")
        _debug(f"  Successfully copied to: {output_path}")
        _debug(f"  Output file exists: {output_path.exists()}")
        _debug(f"  Output file size: {output_path.stat().st_size} bytes")
    except Exception as e:
        LogError(f"Failed to store file: {e}")
        _debug(f"  Copy failed with error: {e}")
        import traceback
        _debug(f"  Traceback: {traceback.format_exc()}")


def AppendNotes(
    notesToAppend: str,
    targetLayerGuid: Optional[str] = None
) -> None:
    """Append notes to a tile set."""
    guid = targetLayerGuid if targetLayerGuid else "default"
    
    if guid not in _notes:
        _notes[guid] = []
    
    _notes[guid].append(notesToAppend)
    print(f"[NOTE] {notesToAppend.strip()}")


def CreateImageLayer(
    layerName: str,
    imageFilePath: str,
    stagePosition: Optional[Tuple[str, str, str]] = None,
    totalSize: Optional[Tuple[str, str]] = None,
    rotation: Optional[str] = None,
    targetLayerGroupName: Optional[str] = None,
    keepFile: Optional[bool] = False
) -> None:
    """
    Create an image layer from an image file.
    
    In real MAPS: Imports image as a layer
    In helper app: Copies image to /output (stub)
    """
    LogInfo(f"CreateImageLayer called: {layerName} from {imageFilePath}")
    # In helper app, just copy to output
    source_path = Path(imageFilePath)
    if source_path.exists():
        # Use OUTPUT_DIR environment variable if set, otherwise default to /output
        output_dir_str = os.environ.get('OUTPUT_DIR', '/output')
        output_dir = Path(output_dir_str)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"layer_{source_path.name}"
        try:
            shutil.copy2(str(source_path), str(output_path))
            LogInfo(f"Image layer created: {output_path.name}")
        except Exception as e:
            LogError(f"Failed to create image layer: {e}")


# ============================================================================
# Annotation Functions
# ============================================================================

def CreateAnnotation(
    annotationName: str,
    stagePosition: Tuple[str, str, str],
    rotation: Optional[str] = "0",
    size: Optional[Tuple[str, str]] = None,
    notes: Optional[str] = "",
    color: Optional[Tuple[int, int, int]] = None,
    isEllipse: Optional[bool] = False,
    targetLayerGroupName: Optional[str] = None
) -> None:
    """
    Create an annotation (SOI or AOI).
    
    In real MAPS: Creates annotation in project
    In helper app: Logs the annotation (stub)
    """
    annotation_type = "AOI" if size else "SOI"
    if targetLayerGroupName:
        LogInfo(f"Created {annotation_type}: {annotationName} at {stagePosition} (Group: {targetLayerGroupName})")
    else:
        LogInfo(f"Created {annotation_type}: {annotationName} at {stagePosition}")


# ============================================================================
# Coordinate Transform Helpers
# ============================================================================

def _row_vector_times_matrix(p: Tuple[float, float, float], m: List[List[float]]) -> Tuple[float, float, float]:
    """
    Multiply row vector p=[x,y,1] by 3x3 matrix m.
    Returns (x', y', w').
    """
    x, y, w = p
    return (
        x * m[0][0] + y * m[1][0] + w * m[2][0],
        x * m[0][1] + y * m[1][1] + w * m[2][1],
        x * m[0][2] + y * m[1][2] + w * m[2][2],
    )


def TilePixelToStage(
    tileImagePixelX: int,
    tileImagePixelY: int,
    tileColumn: int,
    tileRow: int,
    tileSet: TileSetInfo,
) -> PointFloat:
    """
    Convert pixel coordinates within a tile image to stage coordinates (meters).
    Matches Script Bridge documentation.
    """
    # Find tile info
    tile = next((t for t in tileSet.Tiles if t.Column == tileColumn and t.Row == tileRow), None)
    if tile is None:
        raise ValueError(f"Tile not found in TileSet: [{tileColumn}, {tileRow}]")

    m = tileSet.PixelToStageMatrix
    tr = tileSet.TileResolution

    # Pixel coords relative to tile set center
    pixel_x = float(tile.TileCenterPixelOffset.X) - (float(tr.Width) / 2.0) + float(tileImagePixelX)
    # Note opposite sign for stage Y axis per docs
    pixel_y = -float(tile.TileCenterPixelOffset.Y) + (float(tr.Height) / 2.0) - float(tileImagePixelY)

    stage_x, stage_y, _w = _row_vector_times_matrix((pixel_x, pixel_y, 1.0), m)
    return PointFloat(X=stage_x, Y=stage_y)


def ImagePixelToStage(
    imagePixelX: int,
    imagePixelY: int,
    imageLayer: ImageLayerInfo,
) -> PointFloat:
    """
    Convert pixel coordinates within an image layer (stitched image) to stage coordinates (meters).
    Matches Script Bridge documentation.
    """
    m = imageLayer.PixelToStageMatrix
    res = imageLayer.TotalLayerResolution

    pixel_x = -(float(res.Width) / 2.0) + float(imagePixelX)
    pixel_y = (float(res.Height) / 2.0) - float(imagePixelY)

    stage_x, stage_y, _w = _row_vector_times_matrix((pixel_x, pixel_y, 1.0), m)
    return PointFloat(X=stage_x, Y=stage_y)


# ============================================================================
# Logging Functions
# ============================================================================

def LogInfo(infoMessage: str) -> None:
    """Log an info message"""
    print(f"[INFO] {infoMessage}")


def LogWarning(warningMessage: str) -> None:
    """Log a warning message"""
    print(f"[WARNING] {warningMessage}", file=sys.stderr)


def LogError(errorMessage: str) -> None:
    """Log an error message"""
    print(f"[ERROR] {errorMessage}", file=sys.stderr)


def ReportFailure(errorMessage: str) -> None:
    """Report a failure and exit"""
    print(f"[FAILURE] {errorMessage}", file=sys.stderr)
    sys.exit(1)


def ReportActivityDescription(activityDescription: str) -> None:
    """Report activity description"""
    print(f"[ACTIVITY] {activityDescription}")


# ============================================================================
# Tile Filename Helpers
# ============================================================================

def GetTileImageFileName(
    tileRow: int,
    tileColumn: int,
    channelIndex: int,
    planeIndex: int,
    timeFrame: int,
    extension: Optional[str] = None,
    pluginInfo: Optional[str] = None
) -> str:
    """Generate tile image filename matching MAPS convention"""
    ext = f".{extension}" if extension is not None else ".tiff"
    plugin = f".{pluginInfo}" if pluginInfo is not None else ""
    return f"Tile_{tileRow:03d}-{tileColumn:03d}-{planeIndex:06d}_{channelIndex:01d}-{timeFrame:03d}{plugin}{ext}"


def GetTileXtImageFileName(
    tileRow: int,
    tileColumn: int,
    channelIndex: int,
    planeIndex: int,
    timeFrame: int,
    extension: Optional[str] = None,
    slice: Optional[int] = 1,
    energy: Optional[int] = 0
) -> str:
    """Generate XT tile image filename"""
    return GetTileImageFileName(tileRow, tileColumn, channelIndex, planeIndex, timeFrame, extension, f"s{slice:04d}_e{energy:02d}")


def GetTileEdsImageFileName(tileRow: int, tileColumn: int, channelIndex: int) -> str:
    """Generate EDS tile image filename"""
    return GetTileImageFileName(tileRow, tileColumn, channelIndex, 0, 0, "tiff")


# ============================================================================
# Convenience Helper Functions (Optional, May Evolve)
# ============================================================================
# These helpers mirror the convenience helpers shipped with the "real" MAPS
# Script Bridge implementation, but are implemented in a helper-app-friendly way.

def GetTileInfoForTile(tileSet: TileSetInfo, tile: Tile) -> Optional[TileInfo]:
    """
    Find the TileInfo corresponding to a Tile (Column/Row) in a TileSet.
    Returns None if not found.
    """
    return next((t for t in tileSet.Tiles if t.Column == tile.Column and t.Row == tile.Row), None)


def GetTileImagePath(tileSet: TileSetInfo, tileInfo: TileInfo, channelIndex: str = "0") -> str:
    """
    Build the full image file path for a given TileInfo and channel.
    Channel index is treated as a string key (e.g., "0").
    """
    file_name = tileInfo.ImageFileNames[str(channelIndex)]
    return os.path.join(tileSet.DataFolderPath, file_name)


def ResolveSingleTileAndPath(
    request: ScriptTileSetRequest,
    channelIndex: str = "0",
) -> Tuple[Tile, TileInfo, str]:
    """
    For single-tile mode scripts:
    - Uses the first entry in TilesToProcess.
    - Resolves the corresponding TileInfo in SourceTileSet.
    - Returns (Tile, TileInfo, imagePath) for the given channel.
    Raises ValueError if TilesToProcess is empty or tile cannot be resolved.
    """
    if not request.TilesToProcess:
        raise ValueError("TilesToProcess is empty; expected at least one tile.")

    sourceTileSet = request.SourceTileSet
    tile = request.TilesToProcess[0]
    tileInfo = GetTileInfoForTile(sourceTileSet, tile)
    if tileInfo is None:
        raise ValueError(f"TileInfo not found for row={tile.Row}, col={tile.Column}")

    image_path = GetTileImagePath(sourceTileSet, tileInfo, channelIndex)
    return tile, tileInfo, image_path


def IterTileInfosWithPath(
    tileSet: TileSetInfo,
    channelIndex: str = "0",
) -> Iterable[Tuple[TileInfo, str]]:
    """
    Iterate over all tiles in a TileSet, yielding (TileInfo, imagePath) for each tile.
    The channel index is treated as a string key (e.g., "0").
    """
    for tileInfo in tileSet.Tiles:
        file_name = tileInfo.ImageFileNames[str(channelIndex)]
        yield tileInfo, os.path.join(tileSet.DataFolderPath, file_name)


def IterTilesToProcessWithPath(
    request: ScriptTileSetRequest,
    channelIndex: str = "0",
) -> Iterable[Tuple[Tile, TileInfo, str]]:
    """
    Iterate over TilesToProcess in a ScriptTileSetRequest and yield (Tile, TileInfo, imagePath) for each.
    Tiles that cannot be resolved to a TileInfo are skipped.
    """
    tileSet = request.SourceTileSet
    for tile in request.TilesToProcess:
        tileInfo = GetTileInfoForTile(tileSet, tile)
        if tileInfo is None:
            continue
        image_path = GetTileImagePath(tileSet, tileInfo, channelIndex)
        yield tile, tileInfo, image_path


def GetPreparedImagePath(request: ScriptImageLayerRequest, channelIndex: str = "0") -> str:
    """
    Get the prepared image path for a given channel in an image layer request.
    Raises KeyError if the channel is not present.
    """
    key = str(channelIndex)
    try:
        return request.PreparedImages[key]
    except KeyError:
        raise KeyError(f"No prepared image for channel '{key}'")


def ParseScriptParameters(params: Optional[str]) -> Dict[str, str]:
    """
    Parse ScriptParameters into a dictionary.

    Behavior:
      - If params is JSON and parses to a dict, return that (keys and values as strings).
      - Otherwise, support a simple 'key=value;key2=value2' format.
      - Returns {} if params is None or empty.
    """
    if params is None:
        return {}

    text = params.strip()
    if not text:
        return {}

    # Try JSON first
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return {str(k): str(v) for k, v in obj.items()}
    except Exception:
        pass

    # Fallback to key=value;key2=value2
    result: Dict[str, str] = {}
    for part in text.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key.strip()] = value.strip()

    return result


def GetTempOutputFolder(subfolder: str = "MapsScriptOutputs") -> str:
    """
    Get a temp folder path for script outputs and ensure it exists.
    Useful for standardizing where scripts write intermediate results.
    """
    folder = os.path.join(tempfile.gettempdir(), subfolder)
    os.makedirs(folder, exist_ok=True)
    return folder


def GetDefaultOutputTileSetAndChannel(
    sourceTileSet: TileSetInfo,
    channelName: str = "Processed",
    channelColor: Tuple[int, int, int] = (255, 0, 0),
    isAdditive: bool = True,
    targetLayerGroupName: str = "Outputs",
) -> TileSetCreateInfo:
    """
    Convenience helper for a common pattern:
      - Get or create an output tile set named 'Results for <sourceTileSet.Name>'.
      - Ensure the specified channel exists on that tile set with the given color/additivity.
      - Return the TileSetCreateInfo as from GetOrCreateOutputTileSet().
    """
    outputInfo = GetOrCreateOutputTileSet(
        tileSetName=f"Results for {sourceTileSet.Name}",
        tileResolution=None,
        targetLayerGroupName=targetLayerGroupName,
    )

    if outputInfo.TileSet is not None:
        CreateChannel(
            channelName,
            channelColor,
            isAdditive,
            outputInfo.TileSet.Guid,
        )

    return outputInfo


# ============================================================================
# Module initialization
# ============================================================================

if __name__ == "__main__":
    print("MapsBridge shim module - test mode")
    
    request = ScriptTileSetRequest.FromStdIn()
    print(f"Script Name: {request.ScriptName}")
    print(f"Script Parameters: {request.ScriptParameters}")
    print(f"Source Tile Set: {request.SourceTileSet.Name}")
    print(f"Tiles to Process: {len(request.TilesToProcess)}")
