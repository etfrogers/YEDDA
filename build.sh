#!/usr/bin/env bash

source activate YEDDA
pyinstaller --onefile --add-data="version.txt;." YEDDA_Annotator.py
pyinstaller --onefile --add-data="version.txt;." extract_tagged_text.py
mv dist/extract_tagged_text.exe dist/extract_tagged_text_${1}.exe
mv dist/YEDDA_Annotator.exe dist/YEDDA_Annotator_${1}.exe