#!/bin/bash

blueprint-compiler compile ui/window.blp > ui/window.ui
blueprint-compiler compile ui/category-item.blp > ui/category-item.ui
blueprint-compiler compile ui/software-item.blp > ui/software-item.ui

GTK_DEBUG=interactive python -m barrow_software
