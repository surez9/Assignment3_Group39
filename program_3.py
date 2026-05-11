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

# Class 2: ImageProcessor
# Handles all OpenCV image work.
# Loads the original, clones it, and injects
# exactly 5 non-overlapping differences.
# ──────────────────────────────────────────────
class ImageProcessor:
    # How many differences to hide per image
    NUM_DIFFERENCES = 5

    # Minimum and maximum size of each altered patch
    MIN_PATCH = 40
    MAX_PATCH = 90

    def __init__(self):
        self.original_cv = None    # The raw OpenCV image (BGR)
        self.modified_cv = None    # The altered clone
        self.differences = []      # List of Difference objects
        self.display_scale = 1.0   # Scale factor if image is too large

    def load_image(self, filepath):
        """
        Read an image from disk, scale it down if it's huge,
        then generate the modified version with 5 differences.
        """
        img = cv2.imread(filepath)
        if img is None:
            raise ValueError(f"Could not read image: {filepath}")

        # Resize so the game fits on screen without scrolling
        img = self._fit_to_screen(img, max_width=600, max_height=500)

        self.original_cv = img.copy()
        self.modified_cv = img.copy()
        self.differences = []

        self._inject_differences()
        return True

    def _fit_to_screen(self, img, max_width, max_height):
        """Scale down large images while keeping the aspect ratio intact."""
        h, w = img.shape[:2]
        scale = min(max_width / w, max_height / h, 1.0)
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return img

    def _inject_differences(self):
        """
        Create 5 random, non-overlapping difference patches.
        Each one gets a random alteration type and position.
        We keep trying until we place all 5 without overlap.
        """
        h, w = self.original_cv.shape[:2]

        # Five alteration types -- all from class examples
        alteration_types = ["colour_shift", "blur", "brightness", "rotate", "canny"]

        placed = []
        attempts = 0
        max_attempts = 500  # Safety valve so we don't loop forever

        while len(placed) < self.NUM_DIFFERENCES and attempts < max_attempts:
            attempts += 1

            # Pick a random patch size and position
            pw = random.randint(self.MIN_PATCH, self.MAX_PATCH)
            ph = random.randint(self.MIN_PATCH, self.MAX_PATCH)

            # Make sure the patch fits within the image bounds
            if w - pw < 10 or h - ph < 10:
                continue

            px = random.randint(10, w - pw - 10)
            py = random.randint(10, h - ph - 10)

            # Cycle through alteration types so each one appears at least once
            alt_type = alteration_types[len(placed) % len(alteration_types)]

            candidate = Difference(px, py, pw, ph, alt_type)

            # Reject if it overlaps any already-placed difference
            if any(candidate.overlaps(existing) for existing in placed):
                continue

            # Apply the alteration to the modified image
            self._apply_alteration(candidate)
            placed.append(candidate)

        self.differences = placed

    def _apply_alteration(self, diff):
        """
        Alter a rectangular region of the modified image.
        Five types pulled straight from class examples:
        colour shift, blur, brightness, rotate, and canny edge overlay.
        Each is noticeable on careful inspection but not glaringly obvious.
        """
        x, y, w, h = diff.x, diff.y, diff.width, diff.height
        region = self.modified_cv[y:y+h, x:x+w]

        if diff.alteration_type == "colour_shift":
            # Shift the hue by rotating it in HSV space -- from class colour channel work
            hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV).astype(np.int32)
            hsv[:, :, 0] = (hsv[:, :, 0] + random.randint(25, 50)) % 180
            hsv = np.clip(hsv, 0, 255).astype(np.uint8)
            altered = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        elif diff.alteration_type == "blur":
            # Gaussian blur from class -- we used (3,3), (5,5), (33,33) in the notebook
            # We pick a strong kernel so the difference is visible
            ksize = random.choice([11, 13, 15])
            altered = cv2.GaussianBlur(region, (ksize, ksize), 0)

        elif diff.alteration_type == "brightness":
            # Simple pixel value shift -- same idea as the class pixel access examples
            delta = random.choice([-55, -45, 45, 55])
            altered = np.clip(region.astype(np.int32) + delta, 0, 255).astype(np.uint8)

        elif diff.alteration_type == "rotate":
            # cv2.rotate from class -- we saw ROTATE_90_CLOCKWISE in the notebook
            # Pick a random rotation so it's not always the same
            rotation = random.choice([
                cv2.ROTATE_90_CLOCKWISE,
                cv2.ROTATE_90_COUNTERCLOCKWISE,
                cv2.ROTATE_180
            ])
            altered = cv2.rotate(region, rotation)
            # After rotation the shape may flip (w,h) vs (h,w) -- resize back to patch size
            altered = cv2.resize(altered, (w, h), interpolation=cv2.INTER_AREA)

        elif diff.alteration_type == "canny":
            # Canny edge detection from class -- cv2.Canny(image, 100, 200)
            # Detect edges on the patch then overlay them as bright lines
            gray_patch = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_patch, 80, 160)
            # Stack edges back to 3 channels so we can blend with the colour region
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            # Blend: original patch + edge overlay gives a sketchy look
            altered = cv2.addWeighted(region, 0.6, edges_bgr, 0.8, 0)

        else:
            altered = region  # Fallback -- should never hit this

        self.modified_cv[y:y+h, x:x+w] = altered

    def cv_to_tk(self, cv_img):
        """Convert an OpenCV BGR image into a format Tkinter can display."""
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        return ImageTk.PhotoImage(pil_img)

    def draw_circle_on_image(self, cv_img, cx, cy, radius=30, colour=(0, 0, 255)):
        """
        Draw a circle on a copy of the image and return the result.
        Red (0,0,255 in BGR) = found by the player.
        Blue (255,0,0 in BGR) = revealed by the reveal button.
        We draw on a copy so the stored image stays clean.
        """
        result = cv_img.copy()
        cv2.circle(result, (cx, cy), radius, colour, 3)
        return result

    def get_image_size(self):
        """Return (width, height) of the current image."""
        if self.original_cv is None:
            return (0, 0)
        h, w = self.original_cv.shape[:2]
        return (w, h)