# Test-rig image: the app's rathena build stage toolchain + runtime libs, no source baked in.
FROM alpine:3.23
RUN apk add --no-cache bash git make cmake gcc g++ zlib-dev mariadb-dev linux-headers \
        mariadb-connector-c zlib libstdc++ libgcc tzdata mariadb-client python3
