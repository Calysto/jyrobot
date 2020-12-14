# -*- coding: utf-8 -*-
# *************************************
# jyrobot: Python robot simulator
#
# Copyright (c) 2020 Calysto Developers
#
# https://github.com/Calysto/jyrobot
#
# *************************************

import math

from ..utils import Color, Picture


class Camera:
    def __init__(self, robot, config):
        self.robot = robot
        self.cameraShape = [config.get("width", 256), config.get("height", 128)]
        # 0 = no fade, 1.0 = max fade
        self.colorsFadeWithDistance = config.get("colorsFadeWithDistance", 0.5)
        self.sizeFadeWithDistance = config.get("sizeFadeWithDistance", 1.0)
        self.reflectGround = config.get("reflectGround", True)
        self.reflectSky = config.get("reflectSky", False)
        self.set_fov(config.get("angle", 60))  # comes in degrees
        self.reset()

    def reset(self):
        self.hits = [[] for i in range(self.cameraShape[0])]

    def step(self, time_step):
        pass

    def set_fov(self, angle):
        # given in degrees
        # save in radians
        scale = min(max(angle / 6.0, 0.0), 1.0)
        self.angle = angle * math.pi / 180.0
        self.sizeFadeWithDistance = scale
        self.reset()

    def set_size(self, width, height):
        self.cameraShape[0] = width
        self.cameraShape[1] = height
        self.reset()

    def update(self):
        """
        Cameras operate in a lazy way: they don't actually update
        until needed because they are so expensive.
        """
        pass

    def _update(self):
        for i in range(self.cameraShape[0]):
            angle = i / self.cameraShape[0] * self.angle - self.angle / 2
            self.hits[i] = self.robot.castRay(
                self.robot.x,
                self.robot.y,
                math.pi / 2 - self.robot.direction - angle,
                1000,
            )

    def draw(self, canvas):
        canvas.fill(Color(0, 64, 0))
        canvas.strokeStyle(None, 0)
        canvas.rect(5.0, -3.33, 1.33, 6.33)

    def find_closest_wall(self, hits):
        for hit in reversed(hits):  # reverse make it closest first
            if hit.height < 1.0:  # skip non-walls
                continue
            return hit.distance
        return float("inf")

    def takePicture(self, type="color"):
        # Lazy; only get the data when we need it:
        self._update()
        pic = Picture(self.cameraShape[0], self.cameraShape[1])
        size = max(self.robot.world.w, self.robot.world.h)
        hcolor = None
        # draw non-robot walls first:
        for i in range(self.cameraShape[0]):
            hits = [hit for hit in self.hits[i] if hit.height == 1.0]  # only walls
            if len(hits) == 0:
                continue
            hit = hits[-1]  # get closest
            high = None
            hcolor = None
            if hit:
                distance_ratio = max(min(1.0 - hit.distance / size, 1.0), 0.0)
                s = max(
                    min(1.0 - hit.distance / size * self.sizeFadeWithDistance, 1.0), 0.0
                )
                sc = max(
                    min(1.0 - hit.distance / size * self.colorsFadeWithDistance, 1.0),
                    0.0,
                )
                if type == "color":
                    r = hit.color.red * sc
                    g = hit.color.green * sc
                    b = hit.color.blue * sc
                elif type == "depth":
                    r = 255 * distance_ratio
                    g = 255 * distance_ratio
                    b = 255 * distance_ratio
                else:
                    avg = (hit.color.red + hit.color.green + hit.color.blue) / 3.0
                    r = avg * sc
                    g = avg * sc
                    b = avg * sc
                hcolor = Color(r, g, b)
                high = (1.0 - s) * self.cameraShape[1]
            else:
                high = 0

            horizon = self.cameraShape[1] / 2
            for j in range(self.cameraShape[1]):
                dist = max(min(abs(j - horizon) / horizon, 1.0), 0.0)
                if j < high / 2:  # sky
                    if type == "depth":
                        if self.reflectSky:
                            color = Color(255 * dist)
                        else:
                            color = Color(0)
                    elif type == "color":
                        color = Color(0, 0, 128)
                    else:
                        color = Color(128 / 3)
                    pic.set(i, j, color)
                elif j < self.cameraShape[1] - high / 2:  # hit
                    if hcolor is not None:
                        pic.set(i, j, hcolor)
                else:  # ground
                    if type == "depth":
                        if self.reflectGround:
                            color = Color(255 * dist)
                        else:
                            color = Color(0)
                    elif type == "color":
                        color = Color(0, 128, 0)
                    else:
                        color = Color(128 / 3)
                    pic.set(i, j, color)

        # Other robots, draw on top of walls:
        for i in range(self.cameraShape[0]):
            closest_wall_dist = self.find_closest_wall(self.hits[i])
            hits = [hit for hit in self.hits[i] if hit.height < 1.0]  # obstacles
            for hit in hits:
                if hit.distance > closest_wall_dist:
                    # Behind this wall
                    break
                distance_ratio = max(min(1.0 - hit.distance / size, 1.0), 0.0)
                s = max(
                    min(1.0 - hit.distance / size * self.sizeFadeWithDistance, 1.0), 0.0
                )
                sc = max(
                    min(1.0 - hit.distance / size * self.colorsFadeWithDistance, 1.0),
                    0.0,
                )
                distance_to = self.cameraShape[1] / 2 * (1.0 - sc)
                # scribbler was 30, so 0.23 height ratio
                # height is ratio, 0 to 1
                height = round(hit.height * self.cameraShape[1] / 2.0 * s)
                if type == "color":
                    r = hit.color.red * sc
                    g = hit.color.green * sc
                    b = hit.color.blue * sc
                elif type == "depth":
                    r = 255 * distance_ratio
                    g = 255 * distance_ratio
                    b = 255 * distance_ratio
                else:
                    avg = (hit.color.red + hit.color.green + hit.color.blue) / 3.0
                    r = avg * sc
                    g = avg * sc
                    b = avg * sc
                hcolor = Color(r, g, b)
                horizon = self.cameraShape[1] / 2
                for j in range(height):
                    pic.set(i, self.cameraShape[1] - j - 1 - round(distance_to), hcolor)
        return pic