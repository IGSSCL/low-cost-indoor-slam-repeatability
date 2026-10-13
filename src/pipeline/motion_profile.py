# Motion-profile descriptors of a trajectory (speed, acceleration and, when orientations are
# available, the relative rotation between consecutive poses). Taken unchanged from the
# authors' evaluation toolkit (Metricas-Slam, commit 892f6a9, MIT licence). It supplies the
# local-smoothness descriptor S that enters, with L, d_RTO, Delta Z and E_xy, the selection of
# the representative repetition (Section 3.3 of the article and Supplementary Section S8).

import numpy as np


def _relative_rotation_angle(q1_wxyz, q2_wxyz):
    """Rotation angle (rad) between two unit quaternions via dot product."""
    dot = float(np.clip(np.dot(q1_wxyz, q2_wxyz), -1.0, 1.0))
    return 2.0 * np.arccos(np.abs(dot))


def _smooth(arr, window):
    """Apply simple moving average per column with edge-replication padding.

    Uses 'edge' padding so boundary positions are not distorted by
    zero-padding artefacts that would corrupt velocity/acceleration estimates.
    """
    if window < 2 or len(arr) < window:
        return arr.copy()
    pad = window // 2
    kernel = np.ones(window) / window
    out = np.empty_like(arr, dtype=float)
    for col in range(arr.shape[1]):
        padded = np.pad(arr[:, col], pad, mode="edge")
        conv = np.convolve(padded, kernel, mode="valid")
        out[:, col] = conv[: len(arr)]
    return out


def compute_motion_profile(traj, timestamps=None, smooth_window=3, return_arrays=False):
    """Compute velocity and acceleration statistics from a trajectory.

    Args:
        traj: evo PoseTrajectory3D or numpy array of shape [N, 3].
        timestamps: 1-D array of timestamps. Inferred from traj if None.
        smooth_window: Moving-average window applied before differentiation.
        return_arrays: If True, include per-step arrays under "_arrays" key
            (useful for plotting; not intended for JSON serialization).

    Returns:
        dict with "motion_profile" key (and optional "_arrays").
    """
    has_orient = hasattr(traj, "orientations_quat_wxyz")

    if has_orient:
        positions = np.asarray(traj.positions_xyz, dtype=float)
        orientations = np.asarray(traj.orientations_quat_wxyz, dtype=float)
        if timestamps is None:
            timestamps = np.asarray(traj.timestamps, dtype=float)
    else:
        positions = np.asarray(traj, dtype=float)
        orientations = None

    if timestamps is None:
        timestamps = np.arange(len(positions), dtype=float)
    else:
        timestamps = np.asarray(timestamps, dtype=float)

    n = len(positions)
    if n < 3:
        return {
            "motion_profile": None,
            "warnings": ["Trayectoria insuficiente para perfil de movimiento (< 3 poses)."],
        }

    pos_smooth = _smooth(positions, smooth_window)

    # --- velocity [N-1] ---
    dt = np.diff(timestamps)
    dt = np.where(dt < 1e-9, 1e-9, dt)
    dp = np.diff(pos_smooth, axis=0)
    velocities = dp / dt[:, np.newaxis]   # [N-1, 3]
    speed = np.linalg.norm(velocities, axis=1)  # [N-1]

    # --- acceleration [N-2] ---
    dv = np.diff(velocities, axis=0)
    dt2 = np.where(dt[:-1] < 1e-9, 1e-9, dt[:-1])
    accelerations = dv / dt2[:, np.newaxis]  # [N-2, 3]
    acc_norm = np.linalg.norm(accelerations, axis=1)  # [N-2]

    # --- peak events: steps where acc_norm > mean + 2*std ---
    acc_mean = float(np.mean(acc_norm))
    acc_std = float(np.std(acc_norm))
    # Skip peak detection when std is negligible (e.g. perfectly constant velocity)
    # to avoid spurious peaks caused by floating-point noise.
    if acc_std > 1e-6:
        threshold = acc_mean + 2.0 * acc_std
        peak_idx = np.where(acc_norm > threshold)[0]
    else:
        peak_idx = np.array([], dtype=int)
    # timestamps of peaks correspond to index i+1 (midpoint of acceleration interval)
    peak_times = [float(timestamps[i + 1]) for i in peak_idx]

    # --- angular velocity (rad/s) ---
    ang_vel_mean = None
    ang_vel_max = None
    if orientations is not None and len(orientations) >= 2:
        # Vectorized relative rotation angle calculation via quaternion dot product
        q1 = orientations[:-1]
        q2 = orientations[1:]
        dots = np.sum(q1 * q2, axis=1)
        dots = np.clip(dots, -1.0, 1.0)
        ang_rates = 2.0 * np.arccos(np.abs(dots)) / np.maximum(dt, 1e-9)
        ang_vel_mean = float(np.mean(ang_rates))
        ang_vel_max = float(np.max(ang_rates))

    # --- difficulty ---
    n_peaks = len(peak_times)
    if acc_mean > 1.0 or acc_std > 0.5 or n_peaks > 5:
        difficulty = "alta"
    elif acc_mean > 0.3 or acc_std > 0.15 or n_peaks > 2:
        difficulty = "media"
    else:
        difficulty = "baja"

    profile = {
        "velocity_mean": float(np.mean(speed)),
        "velocity_max": float(np.max(speed)),
        "velocity_std": float(np.std(speed)),
        "acc_mean_norm": acc_mean,
        "acc_max_norm": float(np.max(acc_norm)),
        "acc_std_norm": acc_std,
        "acc_x_std": float(np.std(accelerations[:, 0])),
        "acc_y_std": float(np.std(accelerations[:, 1])),
        "acc_z_std": float(np.std(accelerations[:, 2])),
        "peak_event_times": peak_times,
        "difficulty": difficulty,
    }
    if ang_vel_mean is not None:
        profile["angular_velocity_mean"] = ang_vel_mean
        profile["angular_velocity_max"] = ang_vel_max

    out = {"motion_profile": profile}
    if return_arrays:
        # timestamps[1:-1] align with accelerations (length N-2)
        out["_arrays"] = {
            "timestamps_acc": timestamps[1:-1].tolist(),
            "acc_x": accelerations[:, 0].tolist(),
            "acc_y": accelerations[:, 1].tolist(),
            "acc_z": accelerations[:, 2].tolist(),
            "acc_norm": acc_norm.tolist(),
            "timestamps_speed": timestamps[1:].tolist(),
            "speed": speed.tolist(),
        }
    return out
