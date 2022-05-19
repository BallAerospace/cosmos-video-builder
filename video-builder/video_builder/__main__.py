#!/usr/bin/env python3

# Copyright 2022 Ball Aerospace & Technologies Corp.
# All Rights Reserved.
#
# This program is free software; you can modify and/or redistribute it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; version 3 with
# attribution addendums as found in the LICENSE.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# This program may also be used under the terms of a commercial or
# enterprise edition license of COSMOS if purchased from the
# copyright holder

import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import redis
import shlex
import subprocess
import time

from video_builder.config import VideoConfig
from video_builder.environment import *

logging.basicConfig(
  format="%(asctime)s %(levelname)s %(message)s",
  level=logging.getLevelName(logging.INFO),
)

def tick(video_config: VideoConfig, buffer):
  if video_config.stream_ended.is_set():
    logging.info("no more data found, stopping stream")
    return

  try:
    with video_config.mutex:
      count = None if video_config.vfr_scaling_method == "skip" else 1
      
      result = video_config.redis_.xread({
          video_config.stream: video_config.last_frame["stream_id"]
        },
        count=count,
        block=1000
      ) # returns something like [[b"streamname", [(b"1628714734054-0", {b"key0": b"value0", b"key1": b"value1"})]]]

      if result:
        video_config.lag = 0
        entries = result[0][1]
        entry = entries[len(entries) - 1]
        video_config.last_frame["stream_id"] = entry[0].decode("utf-8")
        video_config.last_frame["data"] = entry[1][video_config.key.encode("utf-8")]
      
      elif video_config.last_frame["stream_id"] != "0-0": # Wait for the stream to start before counting lag and deciding to stop
        video_config.lag += 1
        if video_config.lag >= video_config.framerate * 5: # Stop after 5 seconds of no new frames
          video_config.stream_ended.set()
      
      if video_config.last_frame["data"]:
        buffer.write(video_config.last_frame["data"])
  
  except Exception as err:
    logging.exception("failed inside of stream_redis", err)


def stream_redis(video_config: VideoConfig, buffer):
  with ThreadPoolExecutor(max_workers=5) as executor:
    try:
      while video_config.stream_ended.is_set() is not True:
        executor.submit(tick, video_config, buffer)
        with video_config.mutex:
          time.sleep(1 / video_config.framerate)
    
    except (KeyboardInterrupt, SystemExit):
      video_config.stream_ended.set()


def run_ffmpeg(host, stream, key, pix_fmt, resolution, framerate, destination, vfr_scaling_method, codec_preset):
  ffmpeg_args = f"ffmpeg -y -f rawvideo -pix_fmt {pix_fmt} -s {resolution} -r {framerate} -i - -c:v libx264 -preset {codec_preset} -pix_fmt yuv420p -f mpegts \"{destination}\""
  logging.info("> %s", ffmpeg_args)
  command = shlex.split(ffmpeg_args)
  
  try:
    ffmpeg_proc = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    r = redis.Redis(host=host)
    video_config = VideoConfig(redis_=r, stream=stream, key=key, framerate=framerate, vfr_scaling_method=vfr_scaling_method)
    stream_redis(video_config, buffer=ffmpeg_proc.stdin)
    output, error_output = ffmpeg_proc.communicate()
  
    if error_output:
      error_output = error_output.decode("utf-8").strip().rstrip()
  
    resp = output.decode("utf-8").strip().rstrip()
    logging.debug("output from ffmpeg process: %s", resp)
    ffmpeg_proc.stdin.close()
    ffmpeg_proc.wait()
  
  except OSError as e:
    logging.exception("failed to run ffmpeg command.", e)


def main():
  parser = argparse.ArgumentParser(description="Reads pixel values from redis and writes them to a video with ffmpeg")
  parser.add_argument(
    "--host",
    type=str,
    default=COSMOS_VIDEO_HOST,
    help="Hostname for the redis instance"
  )
  parser.add_argument(
    "--stream",
    type=str,
    default=COSMOS_VIDEO_STREAM,
    help="Name of the Redis stream to read from"
  )
  parser.add_argument(
    "--key",
    type=str,
    default=COSMOS_VIDEO_KEY,
    help="Name of the property in `stream` containing the pixel values"
  )
  parser.add_argument(
    "--format",
    type=str,
    default=COSMOS_VIDEO_FORMAT,
    help="The format of the pixel values in redis (see `ffmpeg -pix_fmts`)"
  )
  parser.add_argument(
    "--resolution",
    type=str,
    default=COSMOS_VIDEO_RESOLUTION,
    help="The resolution of the output video"
  )
  parser.add_argument(
    "--framerate",
    type=float,
    default=COSMOS_VIDEO_FRAMERATE,
    help="The framerate of the video"
  )
  parser.add_argument(
    "--destination",
    type=str,
    default=COSMOS_VIDEO_DESTINATION,
    help="The destination of the encoded video"
  )
  parser.add_argument(
    "--vfr_scaling_method",
    type=str,
    default=COSMOS_VIDEO_FRAMERATE_SCALING,
    help="[scale, skip] The type of scaling used to handle incoming frames that are ahead of the CFR clock (default: scale)"
  )
  parser.add_argument(
    "--codec_preset",
    type=str,
    default=COSMOS_VIDEO_CODEC_PRESET,
    help="[ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow] The h.264 encoder preset to use (default: medium)"
  )
  args = parser.parse_args()
  
  run_ffmpeg(args.host, args.stream, args.key, args.format, args.resolution, args.framerate, args.destination, args.vfr_scaling_method, args.codec_preset)
  logging.info("goodbye")


if __name__ == "__main__":
  try:
    main()
  
  except Exception as err:
    logging.error(err)
