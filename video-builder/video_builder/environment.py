#!/usr/bin/env python3

import os

_video_host = "COSMOS_VIDEO_HOST"

_video_stream = "COSMOS_VIDEO_STREAM"

_video_key = "COSMOS_VIDEO_KEY"

_video_format = "COSMOS_VIDEO_FORMAT"

_video_resolution = "COSMOS_VIDEO_RESOLUTION"

_video_framerate = "COSMOS_VIDEO_FRAMERATE"

_video_destination = "COSMOS_VIDEO_DESTINATION"

_video_framerate_scaling = "COSMOS_VIDEO_FRAMERATE_SCALING"

_video_codec_preset = "COSMOS_VIDEO_CODEC_PRESET"

COSMOS_VIDEO_HOST = os.getenv(_video_host, "video-redis")

COSMOS_VIDEO_STREAM = os.getenv(_video_stream, "imagestream")

COSMOS_VIDEO_KEY = os.getenv(_video_key, "pixels")

COSMOS_VIDEO_FORMAT = os.getenv(_video_format, "gray16be")

COSMOS_VIDEO_RESOLUTION = os.getenv(_video_resolution, "1920x1080")

COSMOS_VIDEO_FRAMERATE = os.getenv(_video_framerate, "24")

COSMOS_VIDEO_DESTINATION = os.getenv(_video_destination, "output.mp4")

COSMOS_VIDEO_FRAMERATE_SCALING = os.getenv(_video_framerate_scaling, "scale")

COSMOS_VIDEO_CODEC_PRESET = os.getenv(_video_codec_preset, "medium")
