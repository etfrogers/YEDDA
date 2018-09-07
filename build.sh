#!/usr/bin/env bash

source activate YEDDA
pyinstaller --onefile extract_tagged_text.py
pyinstaller --onefile YEDDA_Annotator.py
mv dist/extract_tagged_text.exe dist/extract_tagged_text_${1}.exe
mv dist/YEDDA_Annotator.exe dist/YEDDA_Annotator_${1}.exe