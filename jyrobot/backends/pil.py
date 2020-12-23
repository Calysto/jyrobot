# -*- coding: utf-8 -*-
# *************************************
# jyrobot: Python robot simulator
#
# Copyright (c) 2020 Calysto Developers
#
# https://github.com/Calysto/jyrobot
#
# *************************************

import io
import math

from PIL import Image, ImageDraw

from ..utils import Color, distance
from .base import Backend


class PILBackend(Backend):
    # Specific to this class:

    def initialize(self):
        self.matrix = []
        self.widget = None
        self.image = Image.new(
            "RGBA", size=(int(self.width * self._scale), int(self.height * self._scale))
        )
        self.draw = ImageDraw.Draw(self.image)

    def update_dimensions(self, width, height, scale):
        self.width = width
        self.height = height
        self._scale = scale
        self.initialize()

    # Canvas API:

    def to_png(self):
        fp = io.BytesIO()
        self.image.save(fp, format="png")
        return fp.getvalue()

    def get_widget(self):
        from ipywidgets import Image

        if self.widget is None:
            self.widget = Image(value=self.to_png())

        return self.widget

    def update(self):
        if self.widget:
            self.widget.value = self.to_png()

    def flush(self):
        pass

    def take_picture(self):
        return self.image

    # High-level API:

    def get_color(self, color):
        if isinstance(color, Color):
            return color.to_tuple()
        else:
            return color

    def get_style(self, style):
        if style == "fill":
            return self.get_color(self.fill_style)
        elif style == "stroke":
            return self.get_color(self.stroke_style)

    def p(self, x, y):
        for matrix in self.matrix:
            for transform in reversed(matrix):
                if transform[0] == "translate":
                    x += transform[1]
                    y += transform[2]
                elif transform[0] == "rotate":
                    dist = distance(0, 0, x, y)
                    angle2 = math.atan2(-x, y)
                    angle = transform[1]
                    x = dist * math.cos(angle2 + angle + math.pi / 2)
                    y = dist * math.sin(angle2 + angle + math.pi / 2)
        return x * self._scale, y * self._scale

    def draw_lines(self, points, stroke_style=None):
        self.stroke_style = stroke_style
        for i in range(len(points)):
            if i < len(points) - 2:
                self.draw_line(
                    points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]
                )

    def draw_line(self, x1, y1, x2, y2):
        p1x, p1y = self.p(x1, y1)
        p2x, p2y = self.p(x2, y2)
        self.draw.line(
            (p1x, p1y, p2x, p2y), fill=self.get_style("stroke"), width=self.line_width
        )

    def clear(self):
        self.fill_style = "white"
        self.draw_rect(0, 0, self.width, self.height)

    def text(self, t, x, y):
        self.draw.text(self.p(x, y), t, fill=self.get_style("fill"))

    def pushMatrix(self):
        self.matrix.append([])

    def popMatrix(self):
        self.matrix.pop()

    def scale(self, x, y):
        pass

    def resetScale(self):
        pass

    def draw_rect(self, x, y, width, height):
        p1x, p1y = self.p(x, y)
        p2x, p2y = self.p(x + width, y + height)
        self.draw.rectangle(
            (p1x, p1y, p2x, p2y), fill=self.get_style("fill"), width=self.line_width
        )

    def draw_ellipse(self, x, y, radiusX, radiusY):
        p1x, p1y = self.p(x - radiusX, y - radiusY)
        p2x, p2y = self.p(x + radiusX, y + radiusY)
        self.draw.ellipse(
            (p1x, p1y, p2x, p2y),
            fill=self.get_style("fill"),
            outline=self.get_style("stroke"),
            width=self.line_width,
        )

    def draw_arc(self, x, y, width, height, startAngle, endAngle):
        p1x, p1y = self.p(x - width, y - height)
        p2x, p2y = self.p(x + width, y + height)
        self.draw.arc(
            (p1x, p1y, p2x, p2y),
            startAngle,
            endAngle,
            fill=self.fill_style,
            width=self.line_width,
        )

    def beginShape(self):
        self.points = []

    def endShape(self):
        self.draw.polygon(
            self.points, fill=self.get_style("fill"), outline=self.get_style("stroke")
        )

    def vertex(self, x, y):
        self.points.append(self.p(x, y))

    def translate(self, x, y):
        self.matrix[-1].append(("translate", x, y))

    def rotate(self, angle):
        self.matrix[-1].append(("rotate", angle))
