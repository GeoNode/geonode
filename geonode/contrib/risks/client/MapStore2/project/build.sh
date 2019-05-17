#!/bin/bash
set -e

npm install
npm run compile
npm run lint
mvn clean install
