
import tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
import random


# Class to create a alter image with difference
class ImageAlteration :
    def __init__(self, region_size = 50):
        self._region_size = region_size

    def get_region_size(self):
        return self._region_size

    def apply(self, img, x, y):
        raise NotImplementedError("Each alteration must implement apply() method")

    def get_roi_bounds(self, img, x, y):
        half = self._region_size // 2
        h, w = img.shape[:2]

        x1 = max(x - half, 0)
        y1 = max(y - half, 0)
        x2 = min(x + half, w)
        y2 = min(y + half, h)
        
        return x1, y1, x2, y2

    def __repr__(self):
        return self.__class__.__name__ + "(region_size=" + str(self._region_size) + ")"

#  Shift the hue of region in HSV space to create difference
class ColourShiftAlteration(ImageAlteration):
    def __init__(self, region_size=50, shift=45):
        super().__init__(region_size)
        self.shift = shift
    
    def apply(self, img, x, y):
        x1, y1, x2, y2 = self.get_roi_bounds(img, x, y)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int32)
        hsv[y1:y2, x1:x2, 0] = (hsv[y1:y2, x1:x2, 0] + self.shift) % 180
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

# Add Gaussian blur to a region
class GaussianBlurAlteration(ImageAlteration):
    def __init__(self, kernel_size=15, region_size=50):
        super().__init__(region_size)
        if kernel_size % 2 == 0:
            kernel_size += 1
        self.kernel_size = kernel_size

    def apply(self, img, x, y):
        x1, y1, x2, y2 = self.get_roi_bounds(img, x, y)
        img[y1:y2, x1:x2] = cv2.GaussianBlur(
            img[y1:y2, x1:x2], (self.kernel_size, self.kernel_size), 0
        )
        return img

# Brightness alteration in image
class BrightnessAlteration(ImageAlteration):


    def __init__(self, beta=60, region_size=50):
        ImageAlteration.__init__(region_size)
        self._beta = beta

    def apply(self, img, x, y):
        x1, y1, x2, y2 = self.get_roi_bounds(img, x, y)
        img[y1:y2, x1:x2] = cv2.convertScaleAbs(
            img[y1:y2, x1:x2], alpha=1.0, beta=self._beta
        )
        return img

# Add pixelate effect to a region
class PixelateAlteration(ImageAlteration):

    def __init__(self, block_size=10, region_size=50):
        super().__init__(region_size)
        self.block_size = max(block_size, 2)

    def apply(self, img, x, y):
        x1, y1, x2, y2 = self.get_roi_bounds(img, x, y)
        roi = img[y1:y2, x1:x2]
        h, w = roi.shape[:2]
        if h < 1 or w < 1:
            return img
        small = cv2.resize(
            roi,
            (max(1, w // self.block_size), max(1, h // self.block_size)),
            interpolation=cv2.INTER_LINEAR,
        )
        img[y1:y2, x1:x2] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        return img

# Load Image in the frame with help of Image Processor
class ImageProcessor:

    IMAGE_SIZE = (400,400)
    NUM_OF_DIFFERENCES = 5
    MIN_SEPARATION = 60

    def __init__(self,image_path):
        self._path = image_path
        original_image = cv2.imread(image_path)
        
        if original_image is None:
            raise FileNotFoundError("Image not found")
        
        self.original_image = cv2.resize(original_image,self.IMAGE_SIZE)
        self.modified_image = None
        self._difference_centres = []

        self._generate_difference()
        

    def get_path(self):
        return self._path
    
    def get_original_image(self):
        return self.original_image.copy()
    
    def get_modified_image(self):
        return self.modified_image.copy()

    def _generate_difference(self):
        alteration_types = [
            ColourShiftAlteration,
            GaussianBlurAlteration,
            BrightnessAlteration,
            PixelateAlteration
        ]       
        self.modified_image = self.original_image.copy()
        self._difference_centres = []
        for _ in range(self.NUM_OF_DIFFERENCES):
            x, y = self._random_point()
            alteration = random.choice(alteration_types)()
            self.modified_image = alteration.apply(self.modified_image, x, y)
            self._difference_centres.append((x, y))
            

    
    def _random_point(self):
        margin = 45
        max_attempts = 1000
        for _ in range(max_attempts):
            x = random.randint(margin, self.IMAGE_SIZE[0]-margin)
            y = random.randint(margin, self.IMAGE_SIZE[1]-margin)
            is_close = False
            for cx, cy in self._difference_centres:
                distance = ((x-cx)**2 + (y-cy)**2)**0.5
                if distance < self.MIN_SEPARATION:
                    is_close = True
                    break
            if not is_close:
                return x, y
        raise RuntimeError("Failed to find a valid point without overlapping")

        
        
    


class GameState:

    MAX_MISTAKES = 3

    def __init__(self, processor: ImageProcessor):
        self.processor = processor
    
    def get_processor(self):
        return self.processor



# Main Application Class
class Application:

    FRAME_SIZE = 400

    def __init__(self, root):
        self.root = root
        self.root.title("Spot the Differences")
        self.root.geometry("850x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")        

        self.game = None

        self.build_ui()

    #  UI for game
    def build_ui(self):
        title = tk.Label(
            self.root,
            text = "Spot the Differences",
            font = ("Helvetica", 16, "bold"),
            bg = "#f0f0f0"
        )
        title.pack(pady=20)

        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(pady=10)

        self.frame_left = tk.Canvas(
            frame,
            width=self.FRAME_SIZE,
            height=self.FRAME_SIZE,
            bg="#e0e0e0",
            bd=0,
            highlightthickness=0
        )
        self.frame_left.grid(row=1, column=0, padx=8)


        self.frame_right = tk.Canvas(
            frame,
            width=self.FRAME_SIZE,
            height=self.FRAME_SIZE,
            bg="#e0e0e0",
            bd=0,
            highlightthickness=0,
            cursor='crosshair'
        )
        self.frame_right.grid(row=1, column=1, padx=8)
        # self.frame_right.bind("<Button-1>", self.on_image_click)
        
        # Button for upload
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Upload Images",
            font = ("Helvetica", 12, "bold"),
            bg = "#4ade80",
            fg = "black",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.upload_images
        ).grid(row=0, column=0, padx=6)


    # Image rendering in the frames

    def cv_to_tk(self,img):
        return ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

    def render_frame(self):
        original_image = self.cv_to_tk(self.game.get_processor().get_original_image())
        modified_image = self.cv_to_tk(self.game.get_processor().get_modified_image())

        self.frame_left.delete('all')
        self.frame_left.create_image(0,0,anchor="nw",image=original_image)
        self.frame_left.photo = original_image

        self.frame_right.delete('all')
        self.frame_right.create_image(0,0,anchor="nw",image=modified_image)
        self.frame_right.photo = modified_image

        
        

    def upload_images(self):
        path = filedialog.askopenfilename(
            title="Select an images", 
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return
        try:
            processor = ImageProcessor(path)
            self.game = GameState(processor)
        except(FileNotFoundError, RuntimeError) as ex:
            messagebox.showerror('Image canot be Loaded', str(ex))
            return
        
        self.render_frame()
        
    

    


# main function call
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()