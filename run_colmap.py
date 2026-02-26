import os
import subprocess
import argparse
import time
import datetime
from shutil import copy2, move
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

@dataclass
class Task:
    """Represents a task to be executed with optional skip paths."""
    name: str
    command: str
    skip_paths: Optional[List[str]] = None
    
    def should_skip(self) -> bool:
        """Check if all skip paths exist."""
        if not self.skip_paths:
            return False
        return all(os.path.exists(path) for path in self.skip_paths)

def rename_image_folder_if_needed(image_path):
    # Rename the image_path folder to "source" if it's named "input" or "images"
    parent_dir = os.path.abspath(os.path.join(image_path, os.pardir))
    current_folder_name = os.path.basename(os.path.normpath(image_path))

    if current_folder_name in ["input", "images"]:
        new_image_path = os.path.join(parent_dir, "source")
        os.rename(image_path, new_image_path)
        print(f"Renamed image folder from {current_folder_name} to: {new_image_path}")
        return new_image_path
    return image_path

def filter_images(image_path, interval):
    parent_dir = os.path.abspath(os.path.join(image_path, os.pardir))
    input_folder = os.path.join(parent_dir, 'input')

    if interval > 1:
        if not os.path.exists(input_folder):
            os.makedirs(input_folder)

        image_files = sorted([f for f in os.listdir(image_path) if os.path.isfile(os.path.join(image_path, f))])
        filtered_files = image_files[::interval]

        for file in filtered_files:
            copy2(os.path.join(image_path, file), os.path.join(input_folder, file))

        return input_folder
    return image_path

def execute_task(task: Task) -> bool:
    """Execute a single task. Returns True if executed, False if skipped."""
    if task.should_skip():
        print(f"Skipping task '{task.name}' - skip paths already exist")
        return False
    
    command_start_time = time.time()
    print(f"Running task '{task.name}'...")
    print(task.command)
    
    try:
        subprocess.run(task.command, shell=True, check=True)
        command_end_time = time.time()
        command_elapsed_time = command_end_time - command_start_time
        print(f"Time taken for task '{task.name}': {command_elapsed_time:.2f} seconds")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Task '{task.name}' failed with error: {e}")
        raise

def extract_frames_from_video(video_path, image_path, fps):
    """Extract frames from a video file using ffmpeg."""
    video_path = os.path.abspath(video_path)
    image_path = os.path.abspath(image_path)
    
    # Create image directory if it doesn't exist
    os.makedirs(image_path, exist_ok=True)
    
    # Build ffmpeg command
    frame_pattern = os.path.join(image_path, 'frame%04d.png')
    command = f'ffmpeg -i "{video_path}" -vf "fps={fps}" "{frame_pattern}"'
    
    # Create and execute task
    task = Task(
        name="Extract Frames from Video",
        command=command,
        skip_paths=[image_path]
    )
    
    execute_task(task)

def run_colmap(image_path, matcher_type, interval, model_type, brush_steps, brush_export_every):
    image_path = os.path.abspath(image_path)
    
    # Rename the image_path folder if needed
    image_path = rename_image_folder_if_needed(image_path)

    parent_dir = os.path.abspath(os.path.join(image_path, os.pardir))
    image_path = filter_images(image_path, interval)

    distorted_folder = os.path.join(parent_dir, 'distorted')
    database_path = os.path.join(distorted_folder, 'database.db')
    sparse_folder = os.path.join(parent_dir, 'sparse')
    sparse_zero_folder = os.path.join(sparse_folder, '0')

    os.makedirs(distorted_folder, exist_ok=True)
    os.makedirs(sparse_folder, exist_ok=True)

    total_start_time = time.time()
    print(f"COLMAP run started at: {datetime.datetime.now()}")

    # Build task list
    tasks = [
        Task(
            name="Feature Extraction",
            command=(
                f"colmap feature_extractor"
                f" --image_path \"{image_path}\" "
                f" --database_path \"{database_path}\""
                f" --ImageReader.single_camera 1"
                f" --ImageReader.camera_model PINHOLE"
            ),
            skip_paths=[database_path]
        ),
        Task(
            name="Feature Matching",
            command=f"colmap {matcher_type} --database_path \"{database_path}\"",
            skip_paths=[]
        ),
        Task(
            name="Mapping",
            command=(
                "glomap mapper"
                f" --database_path \"{database_path}\""
                f" --image_path \"{image_path}\""
                f" --output_path \"{sparse_folder}\""
            ),
            skip_paths=[sparse_zero_folder]
        ),
    ]
    
    # Conditionally add undistortion task for 3dgs model
    if model_type == '3dgs':
        tasks.append(Task(
            name="Image Undistortion",
            command=(
                f"colmap image_undistorter"
                f" --image_path \"{image_path}\""
                f" --input_path \"{sparse_zero_folder}\""
                f" --output_path \"{parent_dir}\""
                f" --output_type COLMAP"
            ),
            skip_paths=[os.path.join(parent_dir, 'images'), os.path.join(sparse_folder, 'frames.bin')]
        ))
        
    brush_folder = os.path.join(parent_dir, 'brush')
    os.makedirs(brush_folder, exist_ok=True)

    tasks.append(Task(
        name="Start Brush training",
        command=(
            "brush_app"
            f" --total-steps {brush_steps}"
            f" --export-every {brush_export_every}"
            f" --export-path \"{brush_folder}\""
            f" \"{parent_dir}\""
        ),
        skip_paths=[os.path.join(brush_folder, '*.ply')]
    ))

    # Execute all tasks
    for task in tasks:
        execute_task(task)

    # Move the cameras.bin, images.bin, and points3D.bin files to sparse/0 in the top-level folder
    os.makedirs(sparse_zero_folder, exist_ok=True)
    for file_name in ['cameras.bin', 'images.bin', 'points3D.bin']:
        source_file = os.path.join(sparse_folder, file_name)
        dest_file = os.path.join(sparse_zero_folder, file_name)
        if os.path.exists(source_file):
            move(source_file, dest_file)
            print(f"Moved {file_name} to {sparse_zero_folder}")

    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time
    print(f"COLMAP run finished at: {datetime.datetime.now()}")
    print(f"Total time taken: {total_elapsed_time:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run COLMAP with specified image path and matcher type.")
    parser.add_argument('--image_path', type=str, default=None, help="Path to the images folder. Required if --video is not provided.")
    parser.add_argument('--video', type=str, default=None, help="Path to a video file to extract frames from. If provided without --image_path, frames will be extracted to 'frames' directory in the same location as the video.")
    parser.add_argument('--fps', type=int, default=10, help="Frames per second for video extraction (default: 10). Only used if --video is provided.")
    parser.add_argument('--matcher_type', default='sequential_matcher', choices=['sequential_matcher', 'exhaustive_matcher'],
                        help="Type of matcher to use (default: sequential_matcher).")
    parser.add_argument('--interval', type=int, default=1, help="Interval of images to use (default: 1, meaning all images).")
    parser.add_argument('--model_type', default='3dgs', choices=['3dgs', 'nerfstudio'],
                        help="Model type to run. '3dgs' (default) includes undistortion, 'nerfstudio' skips undistortion.")
    parser.add_argument('--brush-steps', type=int, default=5000, help="Total training steps for brush (default: 5000).")
    parser.add_argument('--brush-export-every', type=int, default=1000, help="Export model every N steps in brush training (default: 1000).")

    args = parser.parse_args()

    # Validate that either image_path or video is provided
    if not args.image_path and not args.video:
        parser.error("Either --image_path or --video must be provided.")

    # Determine image_path
    image_path = args.image_path
    if args.video:
        if not image_path:
            # Default to 'frames' directory in the same location as the video
            video_dir = os.path.dirname(os.path.abspath(args.video))
            image_path = os.path.join(video_dir, 'frames')
        extract_frames_from_video(args.video, image_path, args.fps)

    run_colmap(image_path, args.matcher_type, args.interval, args.model_type, args.brush_steps, args.brush_export_every)
