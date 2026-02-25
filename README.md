# COLMAP toolbox for generating gaussian splats from video frames

Heavily relies on this tutorial:

[![Tutorial](https://img.youtube.com/vi/A1T9uJtq0cI/0.jpg)](https://www.youtube.com/watch?v=A1T9uJtq0cI)

Steps for video to splats:

1. Extract frames from video
2. Run COLMAP to generate sparse point cloud and camera poses using `run_colmap.py`:
    
```
run_colmap.py --input_path path/to/frames
```

3. Generate splat using [Brush](https://github.com/ArthurBrussee/brush/releases/latest)

## Requires COLMAP

Install COLMAP from compiled releases, and make sure the `colmap.exe` executable is in your PATH

https://github.com/colmap/colmap/releases/tag/latest
