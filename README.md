# Apply Pose as Rest Pose

A minimal Blender extension (4.2+) that applies the current armature pose as the new rest pose, with correct handling of shape keys.

## Features

- Applies the current pose as the rest pose for the active armature and all its child meshes
- Correctly handles meshes with multiple shape keys using depsgraph evaluation and shape key pinning
- Handles meshes with a single basis shape key or no shape keys at all
- Accessible from the sidebar (N panel > Pose tab) or via F3 search

## Installation

Copy the `pose_to_rest` folder into your Blender extensions directory, or install via **Edit > Preferences > Add-ons**.

## Usage

1. Select your armature and enter **Pose Mode**
2. Adjust bones to your desired pose
3. Open the sidebar (N key) and go to the **Pose** tab
4. Click **Apply Pose as Rest Pose**

## License

GPL-3.0-or-later — see [LICENSE](LICENSE) for details.
