# COSMOS video builder

Check out [this gist](https://gist.github.com/ryan-pratt-ball/18f4c69a96c2c88780211ec3848e52b4) to see how this fits into an end-to-end video streaming demo in COSMOS 5.

The purpose of this service is to encode a stream of raw pixel values into a video stream that can be consumed by the COSMOS HLS transcoder microservice. Ideally, it will run as close as possible to the source of the pixel data as to take advantage of video compression for network transport. As such, this is standalone and not a part of COSMOS itself, unlike the [HLS transcoder](https://github.com/BallAerospace/cosmosc2-hls).

## Docker Containers

You start the service by running `control.bat start`. This uses docker-compose to spin up two containers (a frame buffer and en encoder) that are networked together, which make up the video builder service.

### Frame Buffer

Container name: video-builder_video-redis_1

This uses a Redis stream as the frame buffer. Values are written with a command like `_redis.xadd("imagestream", {"pixels": image.tobytes()}, maxlen=100)` with the redis-py client. `imagestream` and `pixels` can be changed as you want with environment variables `COSMOS_VIDEO_STREAM` and `COSMOS_VIDEO_KEY` (discussed later). `image.tobytes()` is the byte array of the pixel values. `maxlen` is the desired number of frames to keep in the buffer. 100 is probably a lot for most scenarios, but it has helped smooth things out while testing this on an underpowered system. With compute resources that can keep up, it only needs to store enough frames for each tick of the encoder - 1 or 2 frames in the case of constant source framerate or the "skip" VFR scaling method (discussed below), and increasing as the variability of the source framerate increases for the "scale" VFR scaling method.

### Encoder

Container name: video-builder_video-builder_1

The encoder is a python module that reads from the frame buffer, has some simple handling of a variable framerate source, and uses an ffmpeg subprocess to encode the video from each frame. It is only tested for outputting an SRT stream, but might work with other stream protocols that support the mpegts container with the h.264 codec and YUV 4:2:0 pixel format.

## VFR Scaling Methods

One requirement for this service is that it can handle inputs with mild to wildly varying framerates (VFR). However, current video standards that are supported by the web do not support this. ffmpeg also assumes that the frames it's given will be at a constant framerate. It has its own frame buffer to handle slight fluctuations, but any major variations need to be handled outside of ffmpeg. The encoder in this service has some basic logic to handle that case. It runs on a clock, ticking once for each frame of the CFR output, specified with `COSMOS_VIDEO_FRAMERATE` variable (see below). The method for handling major fluctuations of the source framerate is specified with the `COSMOS_VIDEO_FRAMERATE_SCALING` variable. In the case that there are no new frames in Redis, the service will duplicate the previous frame regardless of scaling method. After 5 seconds of not receiving a new frame, it will close the stream.

### scale

Use this method if you have a CFR source, or if you want less stuttering in the encoded output from a VFR source. This method is recommended for CFR sources because it will smooth to a 1 frame latency, rather than having stuttering as the framerates become synced (because the clocks of the source and the encoder are not synced).

With this scaling method, the service will read the next single frame from Redis since the last tick. This has the effect of spreading any additional frames that arrived faster than the target framerate over time, which will allow frames to be written instead of a stutter in the event the source framerate temporarily drops below the target framerate. If the actual next frame has fallen out of the Redis frame buffer (because maxlen was too small with a VFR source or because `COSMOS_VIDEO_FRAMERATE` was set too slow), the service will read the oldest frame in the stream and any frames prior will not be in the encoded video stream.

It's important to know approximately what the average source framerate is, and set `COSMOS_VIDEO_FRAMERATE` to that value or higher. Otherwise, the Redis frame buffer will fill up and the encoder won't keep up. If the average source framerate is unknown, use the "skip" VFR scaling method.

### skip

Use this method if you don't know what the average source framerate is, or if you want the output stream to be as close to realtime as possible for every frame, but are ok with more stuttering in the event the source framerate drops below the target framerate.

This method will only use the newest frame in the Redis frame buffer. In the event multiple frames are written since the last encoder tick, the oldest frames will not be ignored (not encoded). Since old frames are omitted, there's no adverse affect to letting them fall out of the buffer, so using a maxlen value of 1 for this scaling method is recommended since it will increase read performance from the Redis frame buffer and decrease memory use.

## Configuration

Configuration is done with a .env file at the same level as the compose.yaml file. The supported variables are:

* COSMOS_VIDEO_HOST: The hostname for the Redis frame buffer. Change this if you're writing to a different Redis instance than the one provided. (Default: video-redis)

* COSMOS_VIDEO_STREAM: The name of the Redis stream containing the frame buffer. (Default: imagestream)

* COSMOS_VIDEO_KEY: The key for the pixel data in an entry of the frame buffer. (Default: pixels)

* COSMOS_VIDEO_FORMAT: The pixel format of the data in the frame buffer. Must be one of ffmpeg's supported formats - see `ffmpeg -formats` for a list of them. (Default: gray16be)

* COSMOS_VIDEO_RESOLUTION: The resolution of the frames. (Default: 1920x1080)

* COSMOS_VIDEO_FRAMERATE: The target output framerate. (Default: 24)

* COSMOS_VIDEO_FRAMERATE_SCALING: The VFR scaling method - either scale or skip. (Default: scale)

    * NOTE: Do not set to "skip" if the source is expected to write frames at a constant framerate. (Either set to "scale" or leave unset.)

* COSMOS_VIDEO_CODEC_PRESET: The h.264 encoder preset. The tradeoff is quality vs. computing power, where slower = higher quality; faster = less computing power required. Aim for the slowest preset you can while still keeping up with the source framerate (which you can monitor in the container logs).
    
    * Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow (Default: medium)

* COSMOS_VIDEO_DESTINATION: The address for the output stream.
    
    * NOTE: This must be set.

    * Example: srt://my.stream.server.hostname:1935?streamid=input/live/teststream
