#!/usr/bin/env python3

# Copyright 2021 Ball Aerospace & Technologies Corp.
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

from threading import Event, RLock

class VideoConfig:

    def __init__(self, redis_, stream, key, framerate, vfr_scaling_method) -> None:
        self.last_frame = {
            'stream_id': '0-0',
            'data': None,
        }
        self.mutex = RLock()
        self.stream_ended = Event()
        self.lag = 0
        self.redis_ = redis_
        self.stream = stream
        self.key = key
        self.framerate = framerate
        self.vfr_scaling_method = vfr_scaling_method
