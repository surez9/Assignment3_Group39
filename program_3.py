"""
Spot the Difference Game
HIT137 Group Assignment 3

A desktop game built with Tkinter and OpenCV.
Two images sit side by side. The right one has 5 hidden differences.
Click on them to win. Miss 3 times and you lose the round.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import random
import math


# ──────────────────────────────────────────────
# Class 1: Difference
# Represents a single hidden difference region.
# Knows its position, whether it's been found,
# and what type of alteration was applied.
# ──────────────────────────────────────────────
class Difference:
    def __init__(self, x, y, width, height, alteration_type):
        # Top-left corner of the difference region
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.alteration_type = alteration_type

        # Track whether the player has found this one
        self.found = False

        # The click detection radius (a bit generous so it's fair)
        self.detection_radius = max(width, height) // 2 + 15

    def get_center(self):
        """Return the centre point of this difference region."""
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        return cx, cy

    def is_clicked(self, click_x, click_y):
        """
        Check if a player's click lands close enough to this difference.
        We use Euclidean distance from the click to the centre of the region.
        """
        cx, cy = self.get_center()
        distance = math.sqrt((click_x - cx) ** 2 + (click_y - cy) ** 2)
        return distance <= self.detection_radius

    def overlaps(self, other, padding=20):
        """
        Make sure two difference regions don't sit on top of each other.
        We add a padding buffer so they stay visually separate.
        """
        return not (
            self.x + self.width + padding < other.x
            or other.x + other.width + padding < self.x
            or self.y + self.height + padding < other.y
            or other.y + other.height + padding < self.y
        )

    def mark_found(self):
        """Mark this difference as found by the player."""
        self.found = True

