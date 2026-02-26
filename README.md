# COLMAP toolbox for generating gaussian splats from video frames

Heavily relies on this tutorial:

[![Tutorial](https://img.youtube.com/vi/A1T9uJtq0cI/0.jpg)](https://www.youtube.com/watch?v=A1T9uJtq0cI)

This script automates the process from video to splat PLY file generation

```
run_colmap.py --video video.mp4
```

It goes through the following tasks automatically:

1. Extracts frames from video using `ffmpeg` (needs to be accessible via PATH)
    - You can specify the frame rate using `--fps` (default is 15)
    
2. Runs COLMAP and GLOMAP to generate sparse point cloud and camera poses (needs `colmap` and `glomap` to be accessible via PATH)
3. Run a [Brush](https://github.com/ArthurBrussee/brush/releases/latest) training session to generate a splat PLY file from the COLMAP output (`brush_app.exe` needs to be accessible via PATH)

    - Control Brush training: `--brush-steps` (default is 5000) and `--brush-export-every` (default is 1000, controls how often to export intermediate PLY files during training)
    
## Install

Install this script all deps using Scoop and my bucket:

```powershell
scoop bucket add h3mul https://github.com/h3mul/h3mul-scoop-bucket
scoop install h3mul/run-colmap-script-git
```

## Dependencies

### COLMAP/GLOMAP

https://github.com/colmap/colmap/releases/tag/latest

https://github.com/colmap/glomap/releases/tag/latest

### FFmpeg

https://www.ffmpeg.org/download.html

### Brush

https://github.com/ArthurBrussee/brush/releases/latest
