#!/bin/env python
import logging

class UsecaseBox:
    def __init__(self, name):
        self.name = name
        self.ucs = []      # Array of UsecaseData

    def __str__(self):
        return "UsecaseBox(name='%s')" % (self.name)


class UsecaseNote:
    def __init__(self, text):
        self.text = text
        self.anchors = [] # List of GUIDs (lines)

    def __str__(self):
        return "UsecaseNote(text='%s..')" % (self.text[:10])


class UsecaseData:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.linked_diagram_id = ""
        self.linked_diagram_name = ""

    def __str__(self):
        return "UsecaseData(name='%s')" % (self.name)


class UsecaseArrow:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def __str__(self):
        return "UsecaseArrow()"


class UsecaseDiagramData:
    def __init__(self, name):
        self.name = name
        self.participants = {}
        self.boxes = {}
        self.ucs = []          # Array of UsecaseData
        self.dependencies = [] # Array of UsecaseArrow (dotted line)
        self.associations = [] # Array of UsecaseArrow (line)
        self.notes = []        # Array of UsecaseNote

    def __str__(self):
        return "UsecaseDiagram(name='%s')" % (self.name)

