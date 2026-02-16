"""
MapsBridge.py - Shim module for MAPS Script Bridge v1.1.0 compatibility

Version: 1.1.0 (API aligned with official Thermo Fisher MapsBridge)
Author: Thermo Fisher Scientific (shim by Maps Script Helper)

This shim matches the official MapsBridge API surface so scripts written for MAPS
run in the helper without modification. PascalCase aliases (FromStdIn, LogInfo,
GetOrCreateOutputTileSet, etc.) are provided for compatibility.

Real MAPS: from_stdin() reads JSON from stdin; output functions send JSON to stdout.
This helper: from_stdin() builds a request from /input images; output functions
write files to /output for the UI. Request/response protocol is not used.
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

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

DEBUG = True

def _debug(msg: str) -> None:
    if DEBUG:
        print(f"[MapsBridge DEBUG] {msg}")


# ============================================================================
# Data Classes - Match real MapsBridge v1.1.0 interface
# ============================================================================

@dataclass
class PointInt:
    x: int
    y: int

    def __getitem__(self, idx):
        return (self.x, self.y)[idx]

    def __len__(self):
        return 2


@dataclass
class PointFloat:
    x: float
    y: float

    def __getitem__(self, idx):
        return (self.x, self.y)[idx]

    def __len__(self):
        return 2


@dataclass
class SizeInt:
    width: int
    height: int

    def __getitem__(self, idx):
        return (self.width, self.height)[idx]

    def __len__(self):
        return 2


@dataclass
class SizeFloat:
    width: float
    height: float

    def __getitem__(self, idx):
        return (self.width, self.height)[idx]

    def __len__(self):
        return 2


@dataclass
class Tile:
    column: int
    row: int

    @property
    def Column(self) -> int:
        return self.column

    @property
    def Row(self) -> int:
        return self.row


@dataclass
class TileInfo:
    column: int
    row: int
    stage_position: PointFloat
    tile_center_pixel_offset: PointInt
    image_file_names: Dict[str, str]

    @property
    def ImageFileNames(self) -> Dict[str, str]:
        return self.image_file_names

    @property
    def Column(self) -> int:
        return self.column

    @property
    def Row(self) -> int:
        return self.row


@dataclass
class ChannelInfo:
    index: int
    name: str
    color: str


@dataclass
class Confirmation:
    is_success: bool
    warning_message: str = ""
    error_message: str = ""


@dataclass
class TileSetInfo:
    guid: uuid.UUID
    name: str
    data_folder_path: str
    column_count: int
    row_count: int
    channel_count: int
    is_completed: bool
    size: SizeFloat
    tile_size: SizeFloat
    tile_resolution: SizeInt
    pixel_format: str
    stage_position: PointFloat
    rotation: float
    pixel_to_stage_matrix: List[List[float]]
    acquisition_stage_position: PointFloat
    acquisition_stage_rotation: float
    acquisition_rotation: float
    horizontal_overlap: float
    vertical_overlap: float
    channels: List[ChannelInfo]
    tiles: List[TileInfo]

    @property
    def DataFolderPath(self) -> str:
        return self.data_folder_path

    @property
    def Tiles(self) -> List[TileInfo]:
        return self.tiles

    @property
    def Guid(self) -> uuid.UUID:
        return self.guid

    @property
    def Name(self) -> str:
        return self.name


@dataclass
class ImageLayerInfo:
    guid: uuid.UUID
    name: str
    stage_position: PointFloat
    rotation: float
    data_folder_path: str
    size: SizeFloat
    total_layer_resolution: SizeInt
    pixel_to_stage_matrix: List[List[float]]
    original_tile_set: Optional[TileSetInfo] = None


@dataclass
class AnnotationInfo:
    guid: uuid.UUID
    name: str
    stage_position: PointFloat
    rotation: float
    size: SizeFloat


@dataclass
class LayerInfo:
    layer_exists: bool
    guid: Optional[uuid.UUID] = None
    name: Optional[str] = None
    layer_type: Optional[str] = None
    layer_info: Any = None


# ============================================================================
# Request Classes
# ============================================================================

class ScriptRequest:
    request_type: str
    request_guid: uuid.UUID
    script_name: str
    script_parameters: str

    def __init__(self, request_type, request_guid, script_name, script_parameters):
        self.request_type = request_type
        self.request_guid = request_guid
        self.script_name = script_name
        self.script_parameters = script_parameters

    @property
    def ScriptParameters(self) -> str:
        return self.script_parameters

    @staticmethod
    def from_stdin() -> "ScriptRequest":
        return read_request_from_stdin()

    # PascalCase alias for MAPS Script Bridge compatibility
    FromStdIn = from_stdin


class ScriptTileSetRequest(ScriptRequest):
    source_tile_set: TileSetInfo
    tiles_to_process: List[Tile]

    def __init__(self, request_type, request_guid, script_name, script_parameters,
                 source_tile_set, tiles_to_process):
        super().__init__(request_type, request_guid, script_name, script_parameters)
        self.source_tile_set = source_tile_set
        self.tiles_to_process = tiles_to_process

    @property
    def SourceTileSet(self) -> TileSetInfo:
        return self.source_tile_set

    @property
    def TilesToProcess(self) -> List[Tile]:
        return self.tiles_to_process

    @staticmethod
    def from_stdin() -> "ScriptTileSetRequest":
        _debug("ScriptTileSetRequest.from_stdin() called")
        input_dir_str = os.environ.get('INPUT_DIR', '/input')
        input_dir = Path(input_dir_str)
        _debug(f"Input directory: {input_dir}, exists: {input_dir.exists()}")

        image_files = _scan_input_images(input_dir)
        script_params = os.environ.get("MAPS_SCRIPT_PARAMETERS", "")

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

        pixel_size_meters = 10e-9
        tile_width_meters = tile_pixel_width * pixel_size_meters
        tile_height_meters = tile_pixel_height * pixel_size_meters

        default_channel = ChannelInfo(index=0, name="Default", color="#FFFFFF")

        tiles = []
        if image_files:
            image_file_names = {}
            for idx, img_path in enumerate(image_files):
                image_file_names[str(idx)] = img_path.name

            tile_info = TileInfo(
                column=1,
                row=1,
                stage_position=PointFloat(x=0.0, y=0.0),
                tile_center_pixel_offset=PointInt(x=0, y=0),
                image_file_names=image_file_names
            )
            tiles.append(tile_info)

        pixel_to_stage_matrix = [
            [pixel_size_meters, 0, 0],
            [0, pixel_size_meters, 0],
            [0, 0, 1]
        ]

        source_tile_set = TileSetInfo(
            guid=uuid.uuid4(),
            name="LocalTestTileSet",
            data_folder_path=str(input_dir),
            column_count=1,
            row_count=1,
            channel_count=1,
            is_completed=True,
            size=SizeFloat(width=tile_width_meters, height=tile_height_meters),
            tile_size=SizeFloat(width=tile_width_meters, height=tile_height_meters),
            tile_resolution=SizeInt(width=tile_pixel_width, height=tile_pixel_height),
            pixel_format=pixel_format,
            stage_position=PointFloat(x=0.0, y=0.0),
            rotation=0.0,
            pixel_to_stage_matrix=pixel_to_stage_matrix,
            acquisition_stage_position=PointFloat(x=0.0, y=0.0),
            acquisition_stage_rotation=0.0,
            acquisition_rotation=0.0,
            horizontal_overlap=0.0,
            vertical_overlap=0.0,
            channels=[default_channel],
            tiles=tiles
        )

        tiles_to_process = [Tile(column=1, row=1)] if tiles else []

        request = ScriptTileSetRequest(
            request_type="TileSetRequest",
            request_guid=uuid.uuid4(),
            script_name="local_test",
            script_parameters=script_params,
            source_tile_set=source_tile_set,
            tiles_to_process=tiles_to_process
        )

        _debug(f"Created ScriptTileSetRequest with {len(tiles)} tiles")
        return request

    # PascalCase alias for MAPS Script Bridge compatibility
    FromStdIn = from_stdin


class ScriptImageLayerRequest(ScriptRequest):
    source_image_layer: ImageLayerInfo
    prepared_images: Dict[str, str]

    def __init__(self, request_type, request_guid, script_name, script_parameters,
                 source_image_layer, prepared_images):
        super().__init__(request_type, request_guid, script_name, script_parameters)
        self.source_image_layer = source_image_layer
        self.prepared_images = prepared_images

    @staticmethod
    def from_stdin() -> "ScriptImageLayerRequest":
        _debug("ScriptImageLayerRequest.from_stdin() called")
        input_dir_str = os.environ.get('INPUT_DIR', '/input')
        input_dir = Path(input_dir_str)
        _debug(f"Input directory: {input_dir}, exists: {input_dir.exists()}")

        image_files = _scan_input_images(input_dir)
        script_params = os.environ.get("MAPS_SCRIPT_PARAMETERS", "")

        layer_pixel_width = 1024
        layer_pixel_height = 1024

        if image_files and HAS_PIL:
            try:
                first_image = Image.open(image_files[0])
                layer_pixel_width, layer_pixel_height = first_image.size
                _debug(f"Extracted image metadata: {layer_pixel_width}x{layer_pixel_height}")
            except Exception as e:
                _debug(f"Failed to extract image metadata: {e}")

        pixel_size_meters = 10e-9
        layer_width_meters = layer_pixel_width * pixel_size_meters
        layer_height_meters = layer_pixel_height * pixel_size_meters

        channels = []
        for idx in range(len(image_files)):
            channel = ChannelInfo(index=idx, name=f"Channel_{idx}", color="#FFFFFF")
            channels.append(channel)

        if not channels:
            channels.append(ChannelInfo(index=0, name="Default", color="#FFFFFF"))

        prepared_images = {}
        for idx, img_path in enumerate(image_files):
            prepared_images[str(idx)] = str(img_path.resolve())

        pixel_to_stage_matrix = [
            [pixel_size_meters, 0, 0],
            [0, pixel_size_meters, 0],
            [0, 0, 1]
        ]

        source_image_layer = ImageLayerInfo(
            guid=uuid.uuid4(),
            name="LocalTestImageLayer",
            stage_position=PointFloat(x=0.0, y=0.0),
            rotation=0.0,
            data_folder_path=str(input_dir),
            size=SizeFloat(width=layer_width_meters, height=layer_height_meters),
            total_layer_resolution=SizeInt(width=layer_pixel_width, height=layer_pixel_height),
            pixel_to_stage_matrix=pixel_to_stage_matrix,
            original_tile_set=None
        )

        request = ScriptImageLayerRequest(
            request_type="ImageLayerRequest",
            request_guid=uuid.uuid4(),
            script_name="local_test",
            script_parameters=script_params,
            source_image_layer=source_image_layer,
            prepared_images=prepared_images
        )

        _debug(f"Created ScriptImageLayerRequest with {len(prepared_images)} prepared images")
        return request

    # PascalCase alias for MAPS Script Bridge compatibility
    FromStdIn = from_stdin


# ============================================================================
# Result / Confirmation Classes
# ============================================================================

@dataclass
class TileSetCreateInfo:
    is_success: bool
    error_message: str
    is_created: bool
    tile_set: Optional[TileSetInfo] = None

    @property
    def TileSet(self) -> Optional[TileSetInfo]:
        return self.tile_set


@dataclass
class ImageLayerCreateInfo:
    is_success: bool
    error_message: str
    image_layer: Optional[ImageLayerInfo] = None


@dataclass
class AnnotationCreateInfo:
    is_success: bool
    error_message: str
    annotation: Optional[AnnotationInfo] = None


# ============================================================================
# Internal State (helper app only)
# ============================================================================

_tile_sets: Dict[str, Dict[str, Any]] = {}
_channels: Dict[str, List[Dict[str, Any]]] = {}
_notes: Dict[str, List[str]] = {}


# ============================================================================
# Generic Request Reader
# ============================================================================

def read_request_from_stdin() -> "ScriptTileSetRequest | ScriptImageLayerRequest | ScriptRequest | None":
    request_type = os.environ.get("MAPS_REQUEST_TYPE", "TileSetRequest")
    _debug(f"read_request_from_stdin() called, request_type={request_type}")

    if request_type == "TileSetRequest":
        return ScriptTileSetRequest.from_stdin()
    elif request_type == "ImageLayerRequest":
        return ScriptImageLayerRequest.from_stdin()
    else:
        return ScriptTileSetRequest.from_stdin()


# ============================================================================
# Tile Set Functions
# ============================================================================

def get_or_create_output_tile_set(
    tile_set_name: Optional[str] = None,
    tile_resolution: Optional[Tuple[int, int]] = None,
    target_layer_group_name: Optional[str] = None,
    request_confirmation: Optional[bool] = True,
    **kwargs
) -> Optional[TileSetCreateInfo]:
    # Accept camelCase kwargs for MAPS script compatibility
    tile_set_name = kwargs.get("tileSetName", tile_set_name)
    tile_resolution = kwargs.get("tileResolution", tile_resolution)
    target_layer_group_name = kwargs.get("targetLayerGroupName", target_layer_group_name)
    request_confirmation = kwargs.get("requestConfirmation", request_confirmation)
    for guid_str, info in _tile_sets.items():
        if info.get("name") == tile_set_name:
            _debug(f"Found existing tile set: {tile_set_name}")
            return TileSetCreateInfo(
                is_success=True,
                error_message="",
                is_created=False,
                tile_set=info.get("tileset_info")
            )

    new_guid = uuid.uuid4()
    tile_set_info = TileSetInfo(
        guid=new_guid,
        name=tile_set_name or "OutputTileSet",
        data_folder_path="/output",
        column_count=1,
        row_count=1,
        channel_count=0,
        is_completed=False,
        size=SizeFloat(width=0.001, height=0.001),
        tile_size=SizeFloat(width=0.001, height=0.001),
        tile_resolution=SizeInt(
            width=tile_resolution[0] if tile_resolution else 1024,
            height=tile_resolution[1] if tile_resolution else 1024
        ),
        pixel_format="Gray8",
        stage_position=PointFloat(x=0.0, y=0.0),
        rotation=0.0,
        pixel_to_stage_matrix=[[1e-9, 0, 0], [0, 1e-9, 0], [0, 0, 1]],
        acquisition_stage_position=PointFloat(x=0.0, y=0.0),
        acquisition_stage_rotation=0.0,
        acquisition_rotation=0.0,
        horizontal_overlap=0.0,
        vertical_overlap=0.0,
        channels=[],
        tiles=[]
    )

    _tile_sets[str(new_guid)] = {
        "name": tile_set_name,
        "layer_group": target_layer_group_name,
        "resolution": tile_resolution,
        "tileset_info": tile_set_info
    }

    log_info(f"Created output tile set: {tile_set_name} (guid: {new_guid})")

    if request_confirmation:
        return TileSetCreateInfo(
            is_success=True,
            error_message="",
            is_created=True,
            tile_set=tile_set_info
        )
    return None


def get_or_create_output_tile_set_async(
    tile_set_name: Optional[str] = None,
    tile_resolution: Optional[Tuple[int, int]] = None,
    target_layer_group_name: Optional[str] = None
):
    get_or_create_output_tile_set(tile_set_name, tile_resolution, target_layer_group_name, request_confirmation=False)


def create_tile_set(
    tile_set_name: str,
    stage_position: Tuple,
    total_size: Tuple,
    rotation=None,
    template_name: Optional[str] = None,
    tile_resolution: Optional[Tuple[int, int]] = None,
    tile_hfw=None,
    pixel_size=None,
    schedule_acquisition: Optional[bool] = None,
    target_layer_group_name: Optional[str] = None,
    request_confirmation: Optional[bool] = True
) -> Optional[TileSetCreateInfo]:
    log_info(f"create_tile_set: {tile_set_name} at {stage_position}, size {total_size}")
    result = get_or_create_output_tile_set(tile_set_name, tile_resolution, target_layer_group_name, request_confirmation)
    return result


def create_tile_set_async(
    tile_set_name: str,
    stage_position: Tuple,
    total_size: Tuple,
    rotation=None,
    template_name: Optional[str] = None,
    tile_resolution: Optional[Tuple[int, int]] = None,
    tile_hfw=None,
    pixel_size=None,
    schedule_acquisition: Optional[bool] = None,
    target_layer_group_name: Optional[str] = None,
):
    create_tile_set(tile_set_name, stage_position, total_size, rotation, template_name,
                    tile_resolution, tile_hfw, pixel_size, schedule_acquisition,
                    target_layer_group_name, request_confirmation=False)


# ============================================================================
# Layer Info
# ============================================================================

def get_layer_info(
    layer_name: str,
    request_full_info: Optional[bool] = False
) -> LayerInfo:
    log_info(f"get_layer_info: {layer_name} (full_info={request_full_info})")
    return LayerInfo(layer_exists=False)


# ============================================================================
# Channel Management
# ============================================================================

def create_channel(
    channel_name: str,
    channel_color: Optional[Tuple[int, int, int]] = (255, 255, 255),
    is_additive: Optional[bool] = False,
    target_tile_set_guid: Optional[uuid.UUID] = None,
    request_confirmation: Optional[bool] = True
) -> Optional[Confirmation]:
    guid = str(target_tile_set_guid) if target_tile_set_guid else "default"

    if guid not in _channels:
        _channels[guid] = []

    _channels[guid].append({
        "name": channel_name,
        "color": channel_color,
        "additive": is_additive
    })

    log_info(f"Created channel: {channel_name} with color {channel_color}")

    if request_confirmation:
        return Confirmation(is_success=True)
    return None


def create_channel_async(
    channel_name: str,
    channel_color: Optional[Tuple[int, int, int]] = (255, 255, 255),
    is_additive: Optional[bool] = False,
    target_tile_set_guid: Optional[uuid.UUID] = None
):
    create_channel(channel_name, channel_color, is_additive, target_tile_set_guid, request_confirmation=False)


# ============================================================================
# Output Functions
# ============================================================================

def send_single_tile_output(
    tile_row: int,
    tile_column: int,
    target_channel_name: str,
    image_file_path: str,
    keep_file: Optional[bool] = False,
    target_tile_set_guid: Optional[uuid.UUID] = None,
    request_confirmation: Optional[bool] = True
) -> Optional[Confirmation]:
    _debug(f"send_single_tile_output() called:")
    _debug(f"  tile_row={tile_row}, tile_column={tile_column}")
    _debug(f"  target_channel_name='{target_channel_name}'")
    _debug(f"  image_file_path='{image_file_path}'")

    source_path = Path(image_file_path)
    output_dir_str = os.environ.get('OUTPUT_DIR', '/output')
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_path.exists():
        log_error(f"Output image not found: {image_file_path}")
        if request_confirmation:
            return Confirmation(is_success=False, error_message=f"File not found: {image_file_path}")
        return None

    try:
        source_resolved = source_path.resolve()
        output_resolved = output_dir.resolve()
        if source_resolved.parent == output_resolved:
            log_info(f"Output already in /output: {source_path.name} (Channel: {target_channel_name}, Tile: [{tile_column}, {tile_row}])")
            if request_confirmation:
                return Confirmation(is_success=True)
            return None
    except Exception:
        pass

    original_name = source_path.name
    ext = source_path.suffix
    safe_channel = "".join(c if c.isalnum() or c in "_-" else "_" for c in target_channel_name)
    output_filename = f"{safe_channel}_{original_name}"
    output_path = output_dir / output_filename

    counter = 1
    while output_path.exists():
        base_name = source_path.stem
        output_filename = f"{safe_channel}_{base_name}_{counter}{ext}"
        output_path = output_dir / output_filename
        counter += 1

    try:
        shutil.copy2(str(source_path), str(output_path))
        log_info(f"Output saved: {output_path.name} (Channel: {target_channel_name}, Tile: [{tile_column}, {tile_row}])")
    except Exception as e:
        log_error(f"Failed to copy output file: {e}")
        if request_confirmation:
            return Confirmation(is_success=False, error_message=str(e))
        return None

    if request_confirmation:
        return Confirmation(is_success=True)
    return None


def send_single_tile_output_async(
    tile_row: int,
    tile_column: int,
    target_channel_name: str,
    image_file_path: str,
    keep_file: Optional[bool] = False,
    target_tile_set_guid: Optional[uuid.UUID] = None
):
    send_single_tile_output(tile_row, tile_column, target_channel_name, image_file_path,
                            keep_file, target_tile_set_guid, request_confirmation=False)


def store_file(
    file_path: str,
    overwrite: Optional[bool] = False,
    keep_file: Optional[bool] = True,
    target_layer_guid: Optional[uuid.UUID] = None,
    request_confirmation: Optional[bool] = True
) -> Optional[Confirmation]:
    _debug(f"store_file() called: {file_path}")

    source_path = Path(file_path)
    output_dir_str = os.environ.get('OUTPUT_DIR', '/output')
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_path.exists():
        log_error(f"store_file: Source file does not exist: {file_path}")
        if request_confirmation:
            return Confirmation(is_success=False, error_message=f"File not found: {file_path}")
        return None

    try:
        source_resolved = source_path.resolve()
        output_resolved = output_dir.resolve()
        if source_resolved.parent == output_resolved:
            log_info(f"File already in /output: {source_path.name}")
            if request_confirmation:
                return Confirmation(is_success=True)
            return None
    except Exception:
        pass

    output_path = output_dir / source_path.name

    if output_path.exists() and not overwrite:
        log_warning(f"File already exists and overwrite=False: {output_path.name}")
        if request_confirmation:
            return Confirmation(is_success=True, warning_message="File already exists, skipped")
        return None

    try:
        shutil.copy2(str(source_path), str(output_path))
        log_info(f"File stored: {output_path.name}")
    except Exception as e:
        log_error(f"Failed to store file: {e}")
        if request_confirmation:
            return Confirmation(is_success=False, error_message=str(e))
        return None

    if request_confirmation:
        return Confirmation(is_success=True)
    return None


def store_file_async(
    file_path: str,
    overwrite: Optional[bool] = False,
    keep_file: Optional[bool] = True,
    target_layer_guid: Optional[uuid.UUID] = None
):
    store_file(file_path, overwrite, keep_file, target_layer_guid, request_confirmation=False)


def append_notes(
    notes_to_append: str,
    target_layer_guid: Optional[uuid.UUID] = None,
    request_confirmation: Optional[bool] = True
) -> Optional[Confirmation]:
    guid = str(target_layer_guid) if target_layer_guid else "default"

    if guid not in _notes:
        _notes[guid] = []

    _notes[guid].append(notes_to_append)
    print(f"[NOTE] {notes_to_append.strip()}")

    if request_confirmation:
        return Confirmation(is_success=True)
    return None


def append_notes_async(
    notes_to_append: str,
    target_layer_guid: Optional[uuid.UUID] = None
):
    append_notes(notes_to_append, target_layer_guid, request_confirmation=False)


def create_image_layer(
    layer_name: str,
    image_file_path: str,
    stage_position=None,
    pixel_position: Optional[Tuple[int, int]] = None,
    total_size=None,
    total_width=None,
    pixel_size=None,
    rotation=None,
    target_layer_group_name: Optional[str] = None,
    keep_file: Optional[bool] = False,
    align_to_source_layer: Optional[bool] = True,
    request_confirmation: Optional[bool] = True
) -> Optional[ImageLayerCreateInfo]:
    log_info(f"create_image_layer: {layer_name} from {image_file_path}")

    source_path = Path(image_file_path)
    if source_path.exists():
        output_dir_str = os.environ.get('OUTPUT_DIR', '/output')
        output_dir = Path(output_dir_str)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"layer_{source_path.name}"
        try:
            shutil.copy2(str(source_path), str(output_path))
            log_info(f"Image layer created: {output_path.name}")
        except Exception as e:
            log_error(f"Failed to create image layer: {e}")
            if request_confirmation:
                return ImageLayerCreateInfo(is_success=False, error_message=str(e))
            return None

    if request_confirmation:
        layer_pixel_width, layer_pixel_height = 1024, 1024
        if source_path.exists() and HAS_PIL:
            try:
                img = Image.open(source_path)
                layer_pixel_width, layer_pixel_height = img.size
            except Exception:
                pass

        pixel_size_meters = 10e-9
        image_layer = ImageLayerInfo(
            guid=uuid.uuid4(),
            name=layer_name,
            stage_position=PointFloat(x=0.0, y=0.0),
            rotation=0.0,
            data_folder_path=str(source_path.parent),
            size=SizeFloat(width=layer_pixel_width * pixel_size_meters, height=layer_pixel_height * pixel_size_meters),
            total_layer_resolution=SizeInt(width=layer_pixel_width, height=layer_pixel_height),
            pixel_to_stage_matrix=[[pixel_size_meters, 0, 0], [0, pixel_size_meters, 0], [0, 0, 1]],
            original_tile_set=None
        )
        return ImageLayerCreateInfo(is_success=True, error_message="", image_layer=image_layer)
    return None


def create_image_layer_async(
    layer_name: str,
    image_file_path: str,
    stage_position=None,
    total_size=None,
    rotation=None,
    target_layer_group_name: Optional[str] = None,
    keep_file: Optional[bool] = False
):
    create_image_layer(layer_name, image_file_path, stage_position, total_size=total_size,
                       rotation=rotation, target_layer_group_name=target_layer_group_name,
                       keep_file=keep_file, request_confirmation=False)


# ============================================================================
# Annotation Functions
# ============================================================================

def create_annotation(
    annotation_name: str,
    stage_position: Tuple,
    rotation=0,
    size=None,
    notes: Optional[str] = None,
    color: Optional[Tuple[int, int, int]] = None,
    is_ellipse: Optional[bool] = False,
    target_layer_group_name: Optional[str] = None,
    request_confirmation: Optional[bool] = True
) -> Optional[AnnotationCreateInfo]:
    annotation_type = "AOI" if size else "SOI"
    if target_layer_group_name:
        log_info(f"Created {annotation_type}: {annotation_name} at {stage_position} (Group: {target_layer_group_name})")
    else:
        log_info(f"Created {annotation_type}: {annotation_name} at {stage_position}")

    if request_confirmation:
        anno_size = SizeFloat(width=0.0, height=0.0)
        if size:
            anno_size = SizeFloat(width=float(str(size[0]).split()[0]) if isinstance(size[0], str) else float(size[0]),
                                  height=float(str(size[1]).split()[0]) if isinstance(size[1], str) else float(size[1]))

        annotation = AnnotationInfo(
            guid=uuid.uuid4(),
            name=annotation_name,
            stage_position=PointFloat(x=float(str(stage_position[0]).split()[0]) if isinstance(stage_position[0], str) else float(stage_position[0]),
                                      y=float(str(stage_position[1]).split()[0]) if isinstance(stage_position[1], str) else float(stage_position[1])),
            rotation=float(rotation) if rotation else 0.0,
            size=anno_size
        )
        return AnnotationCreateInfo(is_success=True, error_message="", annotation=annotation)
    return None


def create_annotation_async(
    annotation_name: str,
    stage_position: Tuple,
    rotation=0,
    size=None,
    notes: Optional[str] = "",
    color: Optional[Tuple[int, int, int]] = None,
    is_ellipse: Optional[bool] = False,
    target_layer_group_name: Optional[str] = None
):
    create_annotation(annotation_name, stage_position, rotation, size, notes, color,
                      is_ellipse, target_layer_group_name, request_confirmation=False)


# ============================================================================
# Coordinate Transform Helpers
# ============================================================================

def get_tile_info(tile_column: int, tile_row: int, tile_set: TileSetInfo) -> Optional[TileInfo]:
    return next((t for t in tile_set.tiles if t.column == tile_column and t.row == tile_row), None)


def tile_pixel_to_stage(
    pixel_x: int,
    pixel_y: int,
    tile_column: int,
    tile_row: int,
    tile_set: TileSetInfo
) -> PointFloat:
    tile = next((t for t in tile_set.tiles if t.column == tile_column and t.row == tile_row), None)
    if tile is None:
        raise ValueError(f"Tile not found in tile set: [{tile_column}, {tile_row}]")

    tile_resolution = tile_set.tile_resolution
    pixel_x_offset = tile.tile_center_pixel_offset.x - (tile_resolution.width / 2) + pixel_x
    pixel_y_offset = -tile.tile_center_pixel_offset.y + (tile_resolution.height / 2) - pixel_y

    m = tile_set.pixel_to_stage_matrix
    stage_x = pixel_x_offset * m[0][0] + pixel_y_offset * m[1][0] + 1 * m[2][0]
    stage_y = pixel_x_offset * m[0][1] + pixel_y_offset * m[1][1] + 1 * m[2][1]

    return PointFloat(x=stage_x, y=stage_y)


def image_pixel_to_stage(
    pixel_x: int,
    pixel_y: int,
    image_layer: ImageLayerInfo
) -> PointFloat:
    pixel_x_offset = -image_layer.total_layer_resolution.width / 2 + pixel_x
    pixel_y_offset = image_layer.total_layer_resolution.height / 2 - pixel_y

    m = image_layer.pixel_to_stage_matrix
    stage_x = pixel_x_offset * m[0][0] + pixel_y_offset * m[1][0] + 1 * m[2][0]
    stage_y = pixel_x_offset * m[0][1] + pixel_y_offset * m[1][1] + 1 * m[2][1]

    return PointFloat(x=stage_x, y=stage_y)


def calculate_total_pixel_position(
    pixel_x: int,
    pixel_y: int,
    tile_column: int,
    tile_row: int,
    tile_set: TileSetInfo
) -> PointInt:
    tile = get_tile_info(tile_column, tile_row, tile_set)

    tile_spacing_x = tile_set.tile_resolution.width * (1 - tile_set.horizontal_overlap)
    tile_spacing_y = tile_set.tile_resolution.height * (1 - tile_set.vertical_overlap)
    total_pixel_width = tile_spacing_x * tile_set.column_count + tile_set.tile_resolution.width * tile_set.horizontal_overlap
    total_pixel_height = tile_spacing_y * tile_set.row_count + tile_set.tile_resolution.height * tile_set.vertical_overlap

    return PointInt(
        x=int(pixel_x - (tile_set.tile_resolution.width / 2) + tile.tile_center_pixel_offset.x + total_pixel_width / 2),
        y=int(pixel_y - (tile_set.tile_resolution.height / 2) + tile.tile_center_pixel_offset.y + total_pixel_height / 2)
    )


# ============================================================================
# Logging & Reporting Functions
# ============================================================================

def log_info(info_message: str) -> None:
    print(f"[INFO] {info_message}")


def log_warning(warning_message: str) -> None:
    print(f"[WARNING] {warning_message}", file=sys.stderr)


def log_error(error_message: str) -> None:
    print(f"[ERROR] {error_message}", file=sys.stderr)


def report_failure(error_message: str) -> None:
    print(f"[FAILURE] {error_message}", file=sys.stderr)
    sys.exit(1)


def report_progress(progress_percentage: float) -> None:
    print(f"[PROGRESS] {progress_percentage:.1f}%")


def report_activity_description(activity_description: str) -> None:
    print(f"[ACTIVITY] {activity_description}")


# ============================================================================
# Tile Filename Helpers
# ============================================================================

def get_tile_image_file_name(
    tile_row: int,
    tile_column: int,
    channel_index: int,
    plane_index: int,
    time_frame: int,
    extension: Optional[str] = None,
    plugin_info: Optional[str] = None
) -> str:
    ext = f".{extension}" if extension is not None else ".tiff"
    plugin = f".{plugin_info}" if plugin_info is not None else ""
    return f"Tile_{tile_row:03d}-{tile_column:03d}-{plane_index:06d}_{channel_index:01d}-{time_frame:03d}{plugin}{ext}"


def get_tile_xt_image_file_name(
    tile_row: int,
    tile_column: int,
    channel_index: int,
    plane_index: int,
    time_frame: int,
    extension: Optional[str] = None,
    slice: Optional[int] = 1,
    energy: Optional[int] = 0
) -> str:
    return get_tile_image_file_name(tile_row, tile_column, channel_index, plane_index, time_frame, extension, f"s{slice:04d}_e{energy:02d}")


def get_tile_eds_image_file_name(tile_row: int, tile_column: int, channel_index: int) -> str:
    return get_tile_image_file_name(tile_row, tile_column, channel_index, 0, 0, "tiff")


# ============================================================================
# Internal Helpers
# ============================================================================

def _scan_input_images(input_dir: Path) -> List[Path]:
    image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.bmp", "*.gif"]
    image_files = []
    if input_dir.exists():
        for ext in image_extensions:
            image_files.extend(input_dir.glob(ext))
            image_files.extend(input_dir.glob(ext.upper()))

        if not image_files:
            _debug("  No standard image extensions found, checking all files...")
            all_files = [f for f in input_dir.iterdir() if f.is_file()]
            excluded = {'.gitkeep', '.ds_store', 'thumbs.db', '.matplotlib'}
            image_files = [f for f in all_files if f.name.lower() not in excluded and not f.name.startswith('.')]

    image_files = sorted(set(image_files))
    _debug(f"Total image files found: {len(image_files)}")
    return image_files


# ============================================================================
# PascalCase aliases for MAPS Script Bridge v1.1.0 compatibility
# (must be after ALL function definitions)
# ============================================================================

LogInfo = log_info
LogWarning = log_warning
LogError = log_error
ReportFailure = report_failure
ReportProgress = report_progress
ReportActivityDescription = report_activity_description
SendSingleTileOutput = send_single_tile_output
SendSingleTileOutputAsync = send_single_tile_output_async
StoreFile = store_file
StoreFileAsync = store_file_async
GetOrCreateOutputTileSet = get_or_create_output_tile_set
GetOrCreateOutputTileSetAsync = get_or_create_output_tile_set_async
CreateTileSet = create_tile_set
CreateTileSetAsync = create_tile_set_async
CreateChannel = create_channel
CreateChannelAsync = create_channel_async
AppendNotes = append_notes
AppendNotesAsync = append_notes_async
ReadRequestFromStdIn = read_request_from_stdin
GetTileInfo = get_tile_info
GetLayerInfo = get_layer_info
CreateImageLayer = create_image_layer
CreateImageLayerAsync = create_image_layer_async
CreateAnnotation = create_annotation
CreateAnnotationAsync = create_annotation_async
TilePixelToStage = tile_pixel_to_stage
ImagePixelToStage = image_pixel_to_stage
CalculateTotalPixelPosition = calculate_total_pixel_position
GetTileImageFileName = get_tile_image_file_name
GetTileXtImageFileName = get_tile_xt_image_file_name
GetTileEdsImageFileName = get_tile_eds_image_file_name


# ============================================================================
# Module initialization
# ============================================================================

if __name__ == "__main__":
    print("MapsBridge shim module v1.1.0 - test mode")

    request = ScriptTileSetRequest.from_stdin()
    print(f"Script Name: {request.script_name}")
    print(f"Script Parameters: {request.script_parameters}")
    print(f"Source Tile Set: {request.source_tile_set.name}")
    print(f"Tiles to Process: {len(request.tiles_to_process)}")
