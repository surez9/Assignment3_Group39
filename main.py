import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import random

class ImageProcessor:
    """
    Handles all OpenCV-based image manipulation and difference generation.
    """
    def __init__(self):
        self.original_bgr = None
        self.modified_bgr = None
        self.differences = [] 

    def load_and_scale(self, path, target_width=500):
        # Loads image using OpenCV and scales while maintaining aspect ratio
        self.original_bgr = cv2.imread(path)
        if self.original_bgr is None:
            raise ValueError("File could not be read as an image.")

        # Calculate aspect ratio scaling 
        h, w = self.original_bgr.shape[:2]
        ratio = target_width / float(w)
        new_dim = (target_width, int(h * ratio))
        self.original_bgr = cv2.resize(self.original_bgr, new_dim)
        self.modified_bgr = self.original_bgr.copy()
        self.differences = []

    def generate_differences(self):
        """
        Creating exactly 5 non-overlapping differences using at least 3 alteration types
        Demonstrating logic for ROI extraction and manipulation.
        """
        h, w = self.modified_bgr.shape[:2]
        diff_size = 30
        
        while len(self.differences) < 5:
            x = random.randint(0, w - diff_size)
            y = random.randint(0, h - diff_size)
            new_rect = (x, y, diff_size, diff_size)

            # Guarantee non-overlapping regions [cite: 29]
            if not any(self._is_overlapping(new_rect, d) for d in self.differences):
                self._apply_random_alteration(x, y, diff_size)
                self.differences.append(new_rect)

    def _is_overlapping(self, rect1, rect2):
        # Helper to check for rectangle overlap
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

    def _apply_random_alteration(self, x, y, size):
        # Applies one of three OpenCV alteration methods[cite: 31, 34].
        roi = self.modified_bgr[y:y+size, x:x+size]
        alt_type = random.choice(['color', 'blur', 'brightness'])

        if alt_type == 'color':
            # Color Shift: Modifying BGR channels 
            roi[:, :, 0] = cv2.add(roi[:, :, 0], 30) # Increase Blue
        elif alt_type == 'blur':
            # Localized blur alteration [cite: 31]
            self.modified_bgr[y:y+size, x:x+size] = cv2.GaussianBlur(roi, (15, 15), 0)
        else:
            # Brightness adjustment [cite: 31]
            self.modified_bgr[y:y+size, x:x+size] = cv2.convertScaleAbs(roi, alpha=1.2, beta=10)

    def get_tk_images(self):
        """Converts OpenCV BGR to Tkinter RGB format[cite: 349]."""
        orig_rgb = cv2.cvtColor(self.original_bgr, cv2.COLOR_BGR2RGB)
        mod_rgb = cv2.cvtColor(self.modified_bgr, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(orig_rgb)), ImageTk.PhotoImage(Image.fromarray(mod_rgb))

class GameState:
    # Manages scoring, mistakes, and victory conditions.
    def __init__(self):
        self.total_score = 0
        self.mistakes = 0
        self.found_indices = set()

    def reset_round(self):
        self.mistakes = 0
        self.found_indices = set()

class DifferenceApp(tk.Tk):
    """
    Main GUI application demonstrating Tkinter layout and event binding.
    Inherits from tk.Tk to show OOP principles[.
    """
    def __init__(self):
        super().__init__()
        self.title("Spot Differences")
        self.processor = ImageProcessor()
        self.state = GameState()
        
        self._setup_ui()

    def _setup_ui(self):
        # Organizes widgets using grid and pack managers
        # Top toolbar for controls [cite: 281]
        self.toolbar = tk.Frame(self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_load = tk.Button(self.toolbar, text="Load Image", command=self.load_image)
        self.btn_load.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_reveal = tk.Button(self.toolbar, text="Reveal", command=self.reveal_differences)
        self.btn_reveal.pack(side=tk.LEFT, padx=5, pady=5)

        # Labels for scoring and mistakes [cite: 42, 50]
        self.lbl_info = tk.Label(self.toolbar, text="Remaining: 5 | Mistakes: 0 | Total Score: 0")
        self.lbl_info.pack(side=tk.RIGHT, padx=10)

        # Side-by-side display area [cite: 38]
        self.display_frame = tk.Frame(self)
        self.display_frame.pack()

        self.canvas_left = tk.Canvas(self.display_frame, bg="gray")
        self.canvas_left.grid(row=0, column=0)
        
        self.canvas_right = tk.Canvas(self.display_frame, bg="gray")
        self.canvas_right.grid(row=0, column=1)
        
        # Bind clicks only to the right image [cite: 40, 212]
        self.canvas_right.bind("<Button-1>", self.on_click)

    def load_image(self):
        # Uses file dialog to select images and resets game state.
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.bmp")])
        if not path: return

        try:
            self.processor.load_and_scale(path)
            self.processor.generate_differences()
            self.state.reset_round()
            self.update_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e} ")

    def update_display(self):
        # Refreshes images and UI labels.
        self.img_left, self.img_right = self.processor.get_tk_images()
        
        self.canvas_left.config(width=self.img_left.width(), height=self.img_left.height())
        self.canvas_left.create_image(0, 0, anchor=tk.NW, image=self.img_left)
        
        self.canvas_right.config(width=self.img_right.width(), height=self.img_right.height())
        self.canvas_right.create_image(0, 0, anchor=tk.NW, image=self.img_right)
        
        self.lbl_info.config(text=f"Remaining: {5-len(self.state.found_indices)} | "
                                  f"Mistakes: {self.state.mistakes} | "
                                  f"Total: {self.state.total_score}")

    def on_click(self, event):
        # Handles click detection with reasonable tolerance.
        if self.state.mistakes >= 3 or len(self.state.found_indices) == 5:
            return

        found_any = False
        for i, (dx, dy, dw, dh) in enumerate(self.processor.differences):
            if i not in self.state.found_indices:
                # Proximity check (center of rect with tolerance) [cite: 44]
                if dx <= event.x <= dx + dw and dy <= event.y <= dy + dh:
                    self.state.found_indices.add(i)
                    self.state.total_score += 1
                    self.draw_feedback(dx, dy, dw, dh, "red")
                    found_any = True
                    break

        if not found_any:
            self.state.mistakes += 1
            if self.state.mistakes >= 3:
                messagebox.showwarning("Game Over", "3 Mistakes! Round Over.")

        self.update_display()
        if len(self.state.found_indices) == 5:
            messagebox.showinfo("Success", "All 5 differences found!")

    def draw_feedback(self, x, y, w, h, color):
        # Draws circles on both original and modified images
        cx, cy = x + w//2, y + h//2
        r = 15
        self.canvas_left.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=3)
        self.canvas_right.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=3)

    def reveal_differences(self):
        # Marks all unfound differences in blue[cite: 56, 57].
        for i, (dx, dy, dw, dh) in enumerate(self.processor.differences):
            if i not in self.state.found_indices:
                self.draw_feedback(dx, dy, dw, dh, "blue")
        self.state.mistakes = 3 # Disable further play
        self.update_display()

if __name__ == "__main__":
    app = DifferenceApp()
    app.mainloop() # Keeps window open 