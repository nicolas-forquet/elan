#!/bin/sh

# Stop on error
set -e

# Check arguments
if [ "$#" -le 1 ]; then
  echo "Missing arguments"
  echo "Usage: ./multi_lang_build.sh input_dir output_dir [optional url prefix]"
  exit -1
fi

# Handle internationalization links on navigation sidebar
sed "s|{{prefix}}|$3|" $1/_templates/globaltoc.html.ref > $1/_templates/globaltoc.html

# Build all languages
sphinx-build -D language=en $1 $2/en
sphinx-build -D language=fr $1 $2/fr

# Remove globaltoc.html after sphinx build
rm $1/_templates/globaltoc.html

# Handle root url to go to default language
sed "s|{{prefix}}|$3|" $1/global_index.html.ref > $2/index.html
