#!/bin/bash

DIR=/docker-entrypoint.d

if [[ -d "$DIR" ]]
then
  /bin/run-parts -v --regex '\.sh$' "$DIR"
fi

exec "$@"
