# Maps Script Helper - Deployment & Path Context

Quick reference for paths, commands, deployment details, and MapsBridge API. Use this for AI context or when onboarding.

---

## EC2 Connection

| Item | Value |
|------|-------|
| **Public IP** | `3.148.188.167` |
| **OS** | Amazon Linux |
| **User** | `ec2-user` |
| **SSH Key** | `C:\Users\greg.clark2\Downloads\firsttest.pem` |

**SSH Command (Windows PowerShell):**
```powershell
ssh -i "C:\Users\greg.clark2\Downloads\firsttest.pem" ec2-user@3.148.188.167
```

---

## Paths

### Local (Windows)
- **Project root:** `c:\project\Maps_Script_Helper_EC2\Maps_Script_Helper`
- **Runner image:** `backend\runner_image\` (contains `MapsBridge.py`, `job_runner.py`)

### EC2 (Amazon Linux)
- **Deploy directory:** `/opt/maps-helper`
- **Data directory:** `/opt/maps-helper/data`
  - `data/outputs` – job output
  - `data/library` – script library images
  - `data/assets` – uploads
  - `data/logs` – logs
  - `data/scripts` – scripts
  - `data/db` – SQLite database

---

## Docker Compose

| File | Use Case |
|------|----------|
| `docker-compose.yml` | Local dev (Windows); uses `C:\project\Python` – do not use on EC2 |
| `docker-compose.prod.yml` | EC2 production; uses Linux paths |

**On EC2, always use:**
```bash
docker compose -f docker-compose.prod.yml <command>
```

---

## EC2 Update Workflow

1. **SSH in:**
   ```powershell
   ssh -i "C:\Users\greg.clark2\Downloads\firsttest.pem" ec2-user@3.148.188.167
   ```

2. **Navigate & pull:**
   ```bash
   cd /opt/maps-helper
   git config --global --add safe.directory /opt/maps-helper   # if needed
   git pull origin main
   ```

3. **Fix ownership (if permission errors):**
   ```bash
   sudo chown -R ec2-user:ec2-user /opt/maps-helper
   ```

4. **Build images** (EC2 buildx may be old; use legacy build):
   ```bash
   docker build -t maps-helper-backend .
   docker build -t py-exec:latest ./backend/runner_image
   ```

5. **Start/restart:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

---

## Application URLs

| Environment | URL |
|-------------|-----|
| **EC2** | http://3.148.188.167:8080 |
| **Local dev** | http://localhost:8000 |

---

## Useful Commands (EC2)

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down

# Rebuild & start (if buildx works)
docker compose -f docker-compose.prod.yml up -d --build

# Or use legacy builder:
DOCKER_BUILDKIT=0 docker compose -f docker-compose.prod.yml up -d --build
```

---

## Key Implementation Notes

- **Input/Output paths:** In Docker mode, the runner uses `/input` and `/output` (mounted by the Docker runner). `job_runner.py` falls back to these when `/work/input` does not exist.
- **MapsBridge:** Handles missing input directory by treating it as empty instead of crashing.
- **Production compose:** Does not mount `C:\project\Python`; uses `./data/*` for persistent storage.

---

## MapsBridge v1.1.0 API Reference

The MapsBridge module provides data structures and utility functions for communication between Python scripts and the Script Bridge interface in Thermo Fisher Scientific Maps. Version 1.1.0 uses **snake_case** naming throughout.

### Script Execution Overview

Scripts are executed by Maps for a source layer (tile set or image layer). Maps sends a JSON request via stdin at script startup containing all context. Scripts send JSON responses via stdout to create outputs, layers, annotations, etc.

The helper app simulates this: `from_stdin()` scans `/input` for images and builds a fake request; output functions copy files to `/output`.

### Data Classes

All properties use snake_case:

| Class | Properties |
|-------|------------|
| `PointInt` | `x`, `y` |
| `PointFloat` | `x`, `y` |
| `SizeInt` | `width`, `height` |
| `SizeFloat` | `width`, `height` |
| `Tile` | `column`, `row` |
| `TileInfo` | `column`, `row`, `stage_position` (PointFloat), `tile_center_pixel_offset` (PointInt), `image_file_names` (dict[str,str]) |
| `ChannelInfo` | `index`, `name`, `color` |
| `Confirmation` | `is_success`, `warning_message`, `error_message` |
| `TileSetInfo` | `guid`, `name`, `data_folder_path`, `column_count`, `row_count`, `channel_count`, `is_completed`, `size`, `tile_size`, `tile_resolution`, `pixel_format`, `stage_position`, `rotation`, `pixel_to_stage_matrix`, `acquisition_stage_position`, `acquisition_stage_rotation`, `acquisition_rotation`, `horizontal_overlap`, `vertical_overlap`, `channels`, `tiles` |
| `ImageLayerInfo` | `guid`, `name`, `stage_position`, `rotation`, `data_folder_path`, `size`, `total_layer_resolution`, `pixel_to_stage_matrix`, `original_tile_set` |
| `AnnotationInfo` | `guid`, `name`, `stage_position`, `rotation`, `size` |
| `LayerInfo` | `layer_exists`, `guid`, `name`, `layer_type`, `layer_info` |

Request classes:

| Class | Properties |
|-------|------------|
| `ScriptRequest` | `request_type`, `request_guid`, `script_name`, `script_parameters` |
| `ScriptTileSetRequest` | (inherits above) + `source_tile_set` (TileSetInfo), `tiles_to_process` (list[Tile]) |
| `ScriptImageLayerRequest` | (inherits above) + `source_image_layer` (ImageLayerInfo), `prepared_images` (dict[str,str]) |

Result classes:

| Class | Properties |
|-------|------------|
| `TileSetCreateInfo` | `is_success`, `error_message`, `is_created`, `tile_set` |
| `ImageLayerCreateInfo` | `is_success`, `error_message`, `image_layer` |
| `AnnotationCreateInfo` | `is_success`, `error_message`, `annotation` |

### Functions

#### Reading requests
```python
request = MapsBridge.ScriptTileSetRequest.from_stdin()
request = MapsBridge.ScriptImageLayerRequest.from_stdin()
request = MapsBridge.read_request_from_stdin()  # auto-detects type
```

#### Tile set output
```python
MapsBridge.get_or_create_output_tile_set(tile_set_name, tile_resolution, target_layer_group_name, request_confirmation) -> TileSetCreateInfo
MapsBridge.create_tile_set(tile_set_name, stage_position, total_size, rotation, template_name, tile_resolution, tile_hfw, pixel_size, schedule_acquisition, target_layer_group_name, request_confirmation) -> TileSetCreateInfo
MapsBridge.create_channel(channel_name, channel_color, is_additive, target_tile_set_guid, request_confirmation) -> Confirmation
MapsBridge.send_single_tile_output(tile_row, tile_column, target_channel_name, image_file_path, keep_file, target_tile_set_guid, request_confirmation) -> Confirmation
```

#### Image layer output
```python
MapsBridge.create_image_layer(layer_name, image_file_path, stage_position, pixel_position, total_size, total_width, pixel_size, rotation, target_layer_group_name, keep_file, align_to_source_layer, request_confirmation) -> ImageLayerCreateInfo
```

#### Annotations
```python
MapsBridge.create_annotation(annotation_name, stage_position, rotation, size, notes, color, is_ellipse, target_layer_group_name, request_confirmation) -> AnnotationCreateInfo
```

#### Layer info
```python
MapsBridge.get_layer_info(layer_name, request_full_info) -> LayerInfo
```

#### Files & notes
```python
MapsBridge.store_file(file_path, overwrite, keep_file, target_layer_guid, request_confirmation) -> Confirmation
MapsBridge.append_notes(notes_to_append, target_layer_guid, request_confirmation) -> Confirmation
```

#### Coordinate transforms
```python
MapsBridge.get_tile_info(tile_column, tile_row, tile_set) -> TileInfo
MapsBridge.tile_pixel_to_stage(pixel_x, pixel_y, tile_column, tile_row, tile_set) -> PointFloat
MapsBridge.image_pixel_to_stage(pixel_x, pixel_y, image_layer) -> PointFloat
MapsBridge.calculate_total_pixel_position(pixel_x, pixel_y, tile_column, tile_row, tile_set) -> PointInt
```

#### Logging & reporting
```python
MapsBridge.log_info(info_message)
MapsBridge.log_warning(warning_message)
MapsBridge.log_error(error_message)
MapsBridge.report_failure(error_message)              # terminates script
MapsBridge.report_progress(progress_percentage)       # 0.0 to 100.0
MapsBridge.report_activity_description(activity_description)
```

#### Async variants (fire-and-forget, no confirmation)
All major functions have `_async` variants that set `request_confirmation=False`:
`get_or_create_output_tile_set_async`, `create_tile_set_async`, `create_channel_async`, `send_single_tile_output_async`, `create_image_layer_async`, `create_annotation_async`, `store_file_async`, `append_notes_async`

### Physical Values & Units

All physical values (float|str) support string representations with units:
- **Length:** `m`, `mm`, `um` (or `μm`), `nm` — e.g. `"30um"`, `"5 mm"`, `"4nm"`
- **Angle:** `deg` (or `°`), `rad` — e.g. `"45 deg"`, `"0.785 rad"`
- **Stage position tuples:** `(x, y, rotation)` — e.g. `(0.001, 0.002, 0)` or `("1mm", "2mm", "30 deg")`
- **Size tuples:** `(width, height)` — e.g. `("10um", "5um")`

### Script Default Parameters

Scripts can embed default parameters in comments (parsed by Maps):
```python
# Default parameters
#{
#"RunMode" : "manual",
#"ScriptMode" : "singletiles",
#"ScriptParameters" : "120"
#}
# Default parameters end
```

Options: `RunMode` (manual/whencompleted/whencompletedblocking/live/liveasync), `ScriptMode` (batch/singletiles), `ScriptParameters` (any string), `PrepareImages` (channel indices, image layer only).

### Example: Tile Set Processing (Single Tile Mode)

```python
import os
import tempfile
import MapsBridge
from PIL import Image

def main():
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set
    tile_to_process = request.tiles_to_process[0]
    tile_info = MapsBridge.get_tile_info(tile_to_process.column, tile_to_process.row, source_tile_set)

    tile_filename = tile_info.image_file_names["0"]
    input_path = os.path.join(source_tile_set.data_folder_path, tile_filename)

    MapsBridge.log_info(f"Processing tile [{tile_info.column}, {tile_info.row}]")

    img = Image.open(input_path).convert("L")
    result = img.point(lambda p: 255 if p > 128 else 0)

    output_folder = os.path.join(tempfile.gettempdir(), "output")
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "result.tif")
    result.save(output_path)

    output_info = MapsBridge.get_or_create_output_tile_set(
        "Results for " + source_tile_set.name,
        target_layer_group_name="Outputs"
    )
    MapsBridge.create_channel("Highlight", (255, 0, 0), True, output_info.tile_set.guid)
    MapsBridge.send_single_tile_output(
        tile_info.row, tile_info.column,
        "Highlight", output_path, True, output_info.tile_set.guid
    )

    MapsBridge.log_info("Done!")

if __name__ == "__main__":
    main()
```

### Example: Image Layer Processing

```python
import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib.cm as cm

def main():
    request = MapsBridge.ScriptImageLayerRequest.from_stdin()
    source_layer = request.source_image_layer
    input_path = request.prepared_images["0"]

    MapsBridge.log_info(f"Processing layer: {source_layer.name}")

    img = Image.open(input_path)
    gray_data = np.array(img)
    normalized = (gray_data - gray_data.min()) / (gray_data.max() - gray_data.min())
    colored = cm.viridis(normalized)
    rgb = (colored[:, :, :3] * 255).astype(np.uint8)
    result = Image.fromarray(rgb)

    output_folder = os.path.join(tempfile.gettempdir(), "false_color_output")
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "result_color.png")
    result.save(output_path)

    create_info = MapsBridge.create_image_layer(
        "Viridis - " + source_layer.name,
        output_path,
        target_layer_group_name="Outputs",
        keep_file=True
    )

    MapsBridge.append_notes("Generated with viridis colormap", create_info.image_layer.guid)
    MapsBridge.log_info("Done!")

if __name__ == "__main__":
    main()
```

### Example: Batch Processing with Annotations

```python
import os
import MapsBridge

def main():
    request = MapsBridge.ScriptTileSetRequest.from_stdin()
    source_tile_set = request.source_tile_set

    for tile_input in source_tile_set.tiles:
        tile_filename = tile_input.image_file_names["0"]
        MapsBridge.log_info(f"Processing tile [{tile_input.column}, {tile_input.row}]")

        # Detect feature at pixel (200, 300)
        stage_coords = MapsBridge.tile_pixel_to_stage(
            200, 300, tile_input.column, tile_input.row, source_tile_set
        )
        MapsBridge.create_annotation(
            f"Feature [{tile_input.column}, {tile_input.row}]",
            (stage_coords.x, stage_coords.y, 0),
            target_layer_group_name="Detected Features"
        )

if __name__ == "__main__":
    main()
```
