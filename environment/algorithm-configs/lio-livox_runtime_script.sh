#!/bin/bash
source /opt/ros/noetic/setup.bash
source /opt/ws/devel/setup.bash
mkdir -p /output/logs
roslaunch lio_livox mid360.launch rviz:=false &
PID_LAUNCH=$!
sleep 4

for _ in $(seq 1 30); do
    if rostopic list >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

cat > /tmp/capture_liolivox_tum.py <<'PY'
#!/usr/bin/env python3
import csv
import signal
import threading

import rospy
from nav_msgs.msg import Odometry

csv_path = "/output/trayectoria_LIO-LIVOX.csv"
tum_path = "/output/trayectoria_LIO-LIVOX.txt"
stop_event = threading.Event()


def shutdown(_signum=None, _frame=None):
    stop_event.set()
    rospy.signal_shutdown("stop requested")


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

rospy.init_node("liolivox_tum_writer", anonymous=True, disable_signals=True)

csv_file = open(csv_path, "w", newline="")
tum_file = open(tum_path, "w")
writer = csv.writer(csv_file)
writer.writerow([
    "%time",
    "field.pose.pose.position.x",
    "field.pose.pose.position.y",
    "field.pose.pose.position.z",
    "field.pose.pose.orientation.x",
    "field.pose.pose.orientation.y",
    "field.pose.pose.orientation.z",
    "field.pose.pose.orientation.w",
])
csv_file.flush()


def on_odom(msg):
    ts = msg.header.stamp.to_sec()
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    writer.writerow([ts, p.x, p.y, p.z, q.x, q.y, q.z, q.w])
    tum_file.write(
        f"{ts:.9f} {p.x:.6f} {p.y:.6f} {p.z:.6f} "
        f"{q.x:.6f} {q.y:.6f} {q.z:.6f} {q.w:.6f}\n"
    )
    csv_file.flush()
    tum_file.flush()


rospy.Subscriber("/livox_odometry_mapped", Odometry, on_odom, queue_size=200)
rate = rospy.Rate(20)
while not rospy.is_shutdown() and not stop_event.is_set():
    rate.sleep()

csv_file.close()
tum_file.close()
PY
chmod +x /tmp/capture_liolivox_tum.py
/tmp/capture_liolivox_tum.py > /output/logs/liolivox_odometry.log 2>&1 &
PID_ODOM=$!

# Guardar PointClouds extraídos del tópico de mapeo global
rosrun pcl_ros pointcloud_to_pcd input:=/livox_full_cloud_mapped _prefix:=/output/mapa_parcial_ _binary:=false &
PID_PCD=$!

sleep 2
rosbag play --clock /dataset/*.bag

sleep 2
kill -INT $PID_LAUNCH
kill -INT $PID_PCD
kill -INT $PID_ODOM
wait $PID_LAUNCH 2>/dev/null || true
wait $PID_PCD 2>/dev/null || true
wait $PID_ODOM 2>/dev/null || true

echo "Uniendo nubes parciales..."
MERGED="/output/mapa_LIO-LIVOX.pcd"
rm -f "$MERGED"
TMP_TXT=$(mktemp)
pts_total=0

shopt -s nullglob
files=( /output/mapa_parcial_*.pcd )

for f in "${files[@]}"; do
    awk 'seen && NF>=4 {print $1, $2, $3, $4} /^DATA[[:space:]]+ascii/{seen=1; next}' "$f" >> "$TMP_TXT"
done

pts_total=$(wc -l < "$TMP_TXT")
if [ "$pts_total" -gt 0 ]; then
    {
        echo "# .PCD v0.7 - Point Cloud Data file format"
        echo "VERSION 0.7"
        echo "FIELDS x y z intensity"
        echo "SIZE 4 4 4 4"
        echo "TYPE F F F F"
        echo "COUNT 1 1 1 1"
        echo "WIDTH ${pts_total}"
        echo "HEIGHT 1"
        echo "VIEWPOINT 0 0 0 1 0 0 0"
        echo "POINTS ${pts_total}"
        echo "DATA ascii"
        cat "$TMP_TXT"
    } > "$MERGED"
fi
chmod a+rw /output/mapa_LIO-LIVOX.pcd /output/trayectoria_LIO-LIVOX.csv /output/trayectoria_LIO-LIVOX.txt 2>/dev/null || true
rm -f "$TMP_TXT" /output/mapa_parcial_*.pcd
