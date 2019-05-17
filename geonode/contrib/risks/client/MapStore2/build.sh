#!/bin/bash
set -e

npm install
npm run compile
npm run cleandoc
npm run lint
npm test
npm run doc
mvn clean install
npm run cleandoc
