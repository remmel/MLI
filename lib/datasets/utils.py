import math
import random
import struct
from typing import List, Tuple

import numpy as np
import torch


def sample_from_timestamps_interpolation(timestamps: List[int],
                                         ref_cameras_number: int,
                                         novel_cameras_number_per_ref: int,
                                         init_cameras_number_per_ref: int = None,
                                         max_len_sequence: int = None,
                                         ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    too_short_sequence = len(timestamps) <= max_len_sequence

    ref_ts = []
    novel_ts = []
    init_ts = []

    for i in range(ref_cameras_number):

        if too_short_sequence:
            first_selected_idx = 0
            last_selected_idx = len(timestamps) - 1
        else:
            first_selected_idx = np.random.randint(
                low=0,
                high=len(timestamps) - max_len_sequence,
            )
            last_selected_idx = first_selected_idx + max_len_sequence - 1

        init_frames_positions = np.round(np.linspace(first_selected_idx,
                                                     last_selected_idx,
                                                     init_cameras_number_per_ref
                                                     )).astype(int)

        remain_frames_positions = [j for j in range(first_selected_idx, last_selected_idx + 1)
                                   if j not in init_frames_positions]

        novel_frames_positions = random.sample(remain_frames_positions,
                                               novel_cameras_number_per_ref)

        remain_frames_positions = [j for j in remain_frames_positions
                                   if j not in novel_frames_positions]

        ref_frames_positions = [random.choice(remain_frames_positions)]

        init_ts.append([timestamps[j] for j in init_frames_positions])
        novel_ts.append([timestamps[j] for j in novel_frames_positions])
        ref_ts.append([timestamps[j] for j in ref_frames_positions])

    return np.array(ref_ts), np.array(init_ts), np.array(novel_ts), too_short_sequence


def sample_from_timestamps_randomly(timestamps: List[int],
                                    ref_cameras_number: int,
                                    novel_cameras_number_per_ref: int,
                                    init_cameras_number_per_ref: int = None,
                                    max_len_sequence: int = None,
                                    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    too_short_sequence = len(timestamps) <= max_len_sequence

    ref_ts = []
    novel_ts = []
    init_ts = []

    for i in range(ref_cameras_number):

        if too_short_sequence:
            first_selected_idx = 0
            last_selected_idx = len(timestamps) - 1
        else:
            first_selected_idx = np.random.randint(
                low=0,
                high=len(timestamps) - max_len_sequence,
            )
            last_selected_idx = first_selected_idx + max_len_sequence - 1

        frames_positions = [j for j in range(first_selected_idx, last_selected_idx + 1)]
        init_frames_positions = random.sample(frames_positions,
                                              init_cameras_number_per_ref)

        remain_frames_positions = [j for j in range(first_selected_idx, last_selected_idx + 1)
                                   if j not in init_frames_positions]

        novel_frames_positions = random.sample(remain_frames_positions,
                                               novel_cameras_number_per_ref)

        remain_frames_positions = [j for j in remain_frames_positions
                                   if j not in novel_frames_positions]

        ref_frames_positions = [random.choice(remain_frames_positions)]

        init_ts.append([timestamps[j] for j in init_frames_positions])
        novel_ts.append([timestamps[j] for j in novel_frames_positions])
        ref_ts.append([timestamps[j] for j in ref_frames_positions])

    return np.array(ref_ts), np.array(init_ts), np.array(novel_ts), too_short_sequence


def sample_from_timestamps_extrapolation(timestamps: List[int],
                                         ref_cameras_number: int,
                                         novel_cameras_number_per_ref: int,
                                         init_cameras_number_per_ref: int = None,
                                         max_len_sequence: int = None,
                                         ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    too_short_sequence = len(timestamps) <= max_len_sequence
    timestamps = np.array(timestamps)
    if too_short_sequence:
        selected_idx = np.random.randint(
            low=0,
            high=len(timestamps),
            size=(ref_cameras_number,
                  init_cameras_number_per_ref + novel_cameras_number_per_ref + 1),
        )
    else:
        first_selected_idx = np.random.randint(
            low=0,
            high=len(timestamps) - max_len_sequence,
            size=(ref_cameras_number, 1),
        )
        selected_idx = first_selected_idx + np.random.randint(
            low=0,
            high=max_len_sequence,
            size=(ref_cameras_number,
                  init_cameras_number_per_ref + novel_cameras_number_per_ref + 1),
        )
    selected_idx = np.sort(selected_idx, axis=1)
    first_source_frame_position = np.random.randint(low=0,
                                                    high=1 + novel_cameras_number_per_ref,
                                                    size=(ref_cameras_number, 1),
                                                    )
    source_frames_positions = first_source_frame_position + np.arange(init_cameras_number_per_ref + 1)
    source_mask = np.zeros(selected_idx.shape, dtype=np.bool)
    np.put_along_axis(source_mask, source_frames_positions, True, axis=1)

    if not novel_cameras_number_per_ref:
        novel_ts = None
    else:
        novel_mask = ~source_mask
        novel_idx = selected_idx[novel_mask].reshape(ref_cameras_number, -1)
        novel_ts = timestamps[novel_idx]

    ref_frame_position = np.random.randint(low=0,
                                           high=init_cameras_number_per_ref + 1,
                                           size=(ref_cameras_number, 1))
    ref_frame_position = np.take_along_axis(source_frames_positions, ref_frame_position, axis=1)
    ref_mask = np.zeros(selected_idx.shape, dtype=np.bool)
    np.put_along_axis(ref_mask, ref_frame_position, True, axis=1)
    ref_idx = selected_idx[ref_mask].reshape(ref_cameras_number, -1)
    ref_ts = timestamps[ref_idx]

    init_mask = source_mask & (~ref_mask)
    init_idx = selected_idx[init_mask].reshape(ref_cameras_number, -1)
    init_ts = timestamps[init_idx]

    return ref_ts, init_ts, novel_ts, too_short_sequence


def sample_from_timestamps_base(timestamps: List[int],
                                ref_cameras_number: int,
                                novel_cameras_number_per_ref: int,
                                init_cameras_number_per_ref: int = None,
                                max_len_sequence: int = None,
                                ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    too_short_sequence = False
    if len(timestamps) <= max_len_sequence:
        too_short_sequence = True
        ref_ts = np.random.choice(timestamps, (ref_cameras_number, 1), replace=True)
        init_ts = np.random.choice(timestamps,
                                   (ref_cameras_number, init_cameras_number_per_ref),
                                   replace=True)
        if not novel_cameras_number_per_ref:
            novel_ts = None
        else:
            novel_ts = np.random.choice(timestamps,
                                        (ref_cameras_number, novel_cameras_number_per_ref),
                                        replace=True)
    else:
        timestamps = np.array(timestamps)
        ref_idx = np.random.randint(low=math.floor(max_len_sequence / 2),
                                    high=len(timestamps) - math.ceil(max_len_sequence / 2),
                                    size=(ref_cameras_number, 1),
                                    )
        ref_ts = timestamps[ref_idx]

        init_idx_offset = np.random.randint(low=-math.floor(max_len_sequence / 2),
                                            high=1 + math.ceil(max_len_sequence / 2),
                                            size=(ref_cameras_number, init_cameras_number_per_ref),
                                            )
        init_idx = ref_idx + init_idx_offset
        init_ts = timestamps[init_idx]

        if not novel_cameras_number_per_ref:
            novel_ts = None
        else:
            novel_idx_offset = np.random.randint(low=-math.floor(max_len_sequence / 2),
                                                 high=1 + math.ceil(max_len_sequence / 2),
                                                 size=(ref_cameras_number, novel_cameras_number_per_ref),
                                                 )
            novel_idx = ref_idx + novel_idx_offset
            novel_ts = timestamps[novel_idx]

    return ref_ts, init_ts, novel_ts, too_short_sequence


def sample_nearest(timestamps_poses,
                   novel_cameras_number_per_ref: int,
                   init_cameras_number_per_ref: int = None,
                   max_len_sequence: int = None,
                   ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    timestamps = set(timestamps_poses.keys())
    # timestamps_poses[..., -1:]
    # dists = np.linalg.norm(tar_cam_locs - ref_cam_locs, axis=1)
    too_short_sequence = len(timestamps) <= max_len_sequence

    center_ts = np.random.choice(list(timestamps), 1, replace=True)[0]
    timestamps.remove(center_ts)
    center_locs = timestamps_poses[center_ts][:, -1]
    distances = []
    for timestamp in timestamps:
        distance = np.linalg.norm(timestamps_poses[timestamp][:, -1] - center_locs)
        distances.append([timestamp, distance])
    distances = sorted(distances, key=lambda x: x[1])[:max_len_sequence]

    timestamps = [x[0] for x in distances]
    random.shuffle(timestamps)
    timestamps = timestamps[:novel_cameras_number_per_ref + init_cameras_number_per_ref]
    novel_ts = np.array([[center_ts] + timestamps[:novel_cameras_number_per_ref]])
    init_ts = np.array([timestamps[novel_cameras_number_per_ref:]])
    ref_ts = np.array([[center_ts]])

    return ref_ts, init_ts, novel_ts, too_short_sequence


def coords_pixel_to_film(points: torch.Tensor,
                         intrinsic: torch.Tensor) -> torch.Tensor:
    """
    Convert from pixel coordinates to film coordinates.

    Args:
        points (torch.Tensor): Bc x Bp x 2
        intrinsic (torch.Tensor): Bc x 3 x 3

    Returns:
        torch.Tensor:  Bc x Bp x 2
    """

    film_coords = (points - intrinsic[:, :-1, -1:].permute(0, 2, 1)) / torch.diagonal(intrinsic[:, :-1, :-1],
                                                                                      dim1=1,
                                                                                      dim2=2).unsqueeze(1)
    return film_coords


def coords_film_to_cam(points: torch.Tensor,
                       depth: Union[torch.Tensor, float, int]) -> torch.Tensor:
    """
    Convert points from film coordinates to camera.
    Since this transformation takes points from 2D space to 3D,
    you need to specify the depth value for each point,
    this value is along the direction axis of the camera’s view.

    Args:
        points (torch.Tensor): Bc x Bp x 2
        depth (Union[torch.Tensor, float, int]): Bc x Bp x 1 or Bc x Bp or 1

    Returns:
        torch.Tensor: Bc x Bp x 3
    """

    if isinstance(depth, (int, float)):
        depth = torch.ones_like(points[..., -1:]) * depth
    elif depth.dim() == 2:
        depth = depth.unsqueeze(-1)
    film_homogenous = torch.cat([points, torch.ones_like(points[..., -1:])], dim=-1)

    return film_homogenous * depth


def polynomialRollingHash(str, m=255, p=31):
    power_of_p = 1
    hash_val = 0

    for i in range(len(str)):
        hash_val = ((hash_val + (ord(str[i]) -
                                 ord('a') + 1) *
                     power_of_p) % m)

        power_of_p = (power_of_p * p) % m

    return int(hash_val)


def rgbFromStr(str):
    hash_r = polynomialRollingHash(str, m=255, p=401)
    hash_g = polynomialRollingHash(str, m=255, p=601)
    hash_b = polynomialRollingHash(str, m=255, p=701)
    return np.array([hash_r, hash_g, hash_b])


def load_colmap_binary_cloud(filename: str) -> np.ndarray:
    """
    See
    https://github.com/colmap/colmap/blob/d84ccf885547c6e91c58b2e5dab8a6a34e636be3/scripts/python/read_write_model.py#L128
    """
    list_points = []

    def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character="<"):
        data = fid.read(num_bytes)
        return struct.unpack(endian_character + format_char_sequence, data)

    with open(filename, "rb") as fid:
        num_points = read_next_bytes(fid, 8, "Q")[0]
        for point_line_index in range(num_points):
            binary_point_line_properties = read_next_bytes(fid, num_bytes=43, format_char_sequence="QdddBBBd")
            xyz = np.array(binary_point_line_properties[1:4])
            track_length = read_next_bytes(
                fid, num_bytes=8, format_char_sequence="Q")[0]
            track_elems = read_next_bytes(
                fid, num_bytes=8 * track_length,
                format_char_sequence="ii" * track_length)

            list_points.append(xyz)
    return np.stack(list_points, axis=0)
