FROM ubuntu:latest
LABEL authors="vss"

ENTRYPOINT ["top", "-b"]