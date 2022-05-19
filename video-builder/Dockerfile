FROM ryanpratt/ffmpeg:enable-srt

# We require a local certificate file so set that up.
# You must place a valid cert.pem file in your COSMOS development folder for this work
# Comment out these lines if this is not required in your environment
COPY --from=enterprise-cosmos /devel/cacert.pem /devel/cacert.pem
ENV SSL_CERT_FILE=/devel/cacert.pem
ENV CURL_CA_BUNDLE=/devel/cacert.pem
ENV REQUESTS_CA_BUNDLE=/devel/cacert.pem
ENV NOKOGIRI_USE_SYSTEM_LIBRARIES=1

WORKDIR /cosmos/plugins/video-builder/

RUN apk update \
  && apk add --update \
    python3 \
    ca-certificates \
    libressl \
    less \
    tini \
    git \
  && apk add --virtual .build-dependencies \
    python3-dev \
    build-base \
    libressl-dev \
    libressl-dev \
  && git config --global http.sslCAinfo /devel/cacert.pem \
  && python3 -m ensurepip \
  && pip3 install --no-cache --upgrade pip \
    redis \
  && apk del .build-dependencies \
  && rm -rf \
    /var/cache/apk/* \
    /tmp/* \
    /var/tmp/*

COPY ./ ./

ENTRYPOINT [ "tini" ]

CMD ["python3", "-m", "video_builder"]
