#!/bin/bash

pandoc "COMP_3000_Dissertation.md" -o "HAND_IN/COMP_3000_Dissertation.pdf" \
    --pdf-engine=xelatex \
    --from markdown+raw_tex \
    -V geometry:margin=1in \
    --listings \
    --toc \
    --toc-depth=3

echo "Rendered: HAND_IN/COMP_3000_Dissertation.pdf"