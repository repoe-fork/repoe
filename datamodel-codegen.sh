#!/bin/bash

all=(RePoE/schema/*)
files=("${@:-${all[@]}}")
for file in "${files[@]}"
do
  out=$(basename $file)
  poetry run datamodel-codegen --input $file --input-file-type jsonschema --output RePoE/model/${out/.json/.py} --output-model-type pydantic_v2.BaseModel --disable-timestamp --use-double-quotes --enable-version-header
done
