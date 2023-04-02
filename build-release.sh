#!/bin/sh
docker buildx build --target=export --output=. .
