
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
        super().__init__(region_size)
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
            raise FileNotFoundError("Image not found: "+ image_path)
        
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

    def get_difference_centres(self):
        return list(self._difference_centres)

    # Apply NUM_OF_DIFFERENCES of random alternations
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

        
# keep track of game states and encapsulates all mutable data 
class GameState:

    MAX_MISTAKES = 3
    SCORE_HIT = 20
    SCORE_MISS = -10

    def __init__(self, processor: ImageProcessor):
        self.processor = processor
        self.found = []
        self.mistakes = 0
        self.score = 0
    
    def get_processor(self):
        return self.processor

    def get_found(self):
        return list(self.found)

    def get_mistakes(self):
        return self.mistakes

    def get_score(self):
        return self.score
    
    def get_remaining(self):
        return ImageProcessor.NUM_OF_DIFFERENCES - len(self.found)
    
    def is_complete(self):
        return len(self.found) == ImageProcessor.NUM_OF_DIFFERENCES

    def is_failed(self):
        return self.mistakes >= GameState.MAX_MISTAKES
    
    def is_active(self):
        return not self.is_complete() and not self.is_failed()

    # returns true if click lands on an unfound difference, 
    # updates the score and mistake count accordingly 
    def register_click(self, x, y, radius = 25):
        for dx, dy in self.processor.get_difference_centres():
            if (dx, dy) not in self.found:
                dist = ((x - dx) ** 2 + (y - dy) ** 2) ** 0.5
                if dist <= radius:
                    self.found.append((dx, dy))
                    self.score += self.SCORE_HIT
                    return True
        self.mistakes += 1
        self.score += self.SCORE_MISS
        if self.score < 0:
            self.score = 0
        return False



# Main Application Class
class Application:

    FRAME_SIZE = 400

    def __init__(self, root):
        self.root = root
        self.root.title("Group 39 - Spot the Differences")
        self.root.geometry("850x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")        

        self.game = None
        self.build_ui()

    #  UI for game
    def build_ui(self):
        title = tk.Label(
            self.root,
            text = "CAN YOU FIND THE 5 DIFFERENCES?",
            font = ("Helvetica", 16, "bold"),
            bg = "#f0f0f0"
        )
        title.pack(pady=20)

        frame = tk.Frame(self.root, bg="#f0f0f0") # Created a frame to hold the two iamges
        frame.pack(pady=10)

        tk.Label(frame, text="ORIGINAL IMAGE", fg="#0e2943",
                font=("Courier New", 14, "bold")).grid(row=0, column=0)
        tk.Label(frame, text="MODIFIED IMAGE",
                 fg="#e94560",
                 font=("Courier New", 14, "bold")).grid(row=0, column=1)

        # frame to hold the original image
        self.frame_left = tk.Canvas(
            frame,
            width=self.FRAME_SIZE,
            height=self.FRAME_SIZE,
            bg="#e0e0e0",
            bd=0,
            highlightthickness=0
        )
        self.frame_left.grid(row=1, column=0, padx=8)

        # frame to hold the modified image
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
        self.frame_right.bind("<Button-1>", self.on_image_click)    # Bind the click event to the frame
    
        self.info = tk.StringVar()
        self.info.set("Upload an image to start!")
        info_bar = tk.Label(
            self.root,
            textvariable = self.info,
            font = ("Helvetica", 16),
            bg = "#f0f0f0"
        )
        info_bar.pack(fill=tk.X, pady=20)

        self.status = tk.StringVar()
        tk.Label(
            self.root,
            textvariable = self.status,
            font = ("Helvetica", 14),
            fg="#ff0000",
            bg = "#f0f0f0"
        ).pack()
        
        # Buttons
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=10)

        btn_cfg = {"font": ("Helvetica", 12, "bold"), "width": 16,
                   "relief": tk.FLAT, "padx": 20,'pady':10, 'cursor':'hand2'}

        tk.Button(
            button_frame,
            text="Upload Images",
            bg = "#07f919", 
            fg = "black",
            command=self.upload_images, **btn_cfg
        ).grid(row=0, column=0, padx=6)

        tk.Button(
            button_frame,
            text='Reveal All',
            bg="#07b50f", 
            fg="black",
            command=self.reveal_all, **btn_cfg
        ).grid(row=0, column=1, padx=6)


        tk.Button(
            button_frame, 
            text="Restart",
            bg="#07b50f", 
            fg="black",
            command=self.restart, **btn_cfg
        ).grid(row=0, column=2, padx=6)


    
    def on_image_click(self, event):
        if not self.game or not self.game.is_active():
            return

        click = self.game.register_click(event.x, event.y)

        if click:
            r = 28
            for frame in (self.frame_left, self.frame_right):
                frame.create_oval(
                    event.x-r, event.y-r,
                    event.x+r, event.y+r,
                    outline="#ff4757", width=3
                )
            if self.game.is_complete():
                self.end_round('win')
        else:
            if self.game.is_failed():
                self.end_round('mistakes')
            else:
                remaining_guesses = GameState.MAX_MISTAKES - self.game.get_mistakes()
                messagebox.showwarning(
                    "Wrong!",
                    "Not a difference here.\nYou have " +
                    str(remaining_guesses) + " guess(es) left.", parent = self.root
                )
        
        self.refresh_info()

    def refresh_info(self):
        if not self.game:
            return
        self.info.set(
              "Remaining: " + str(self.game.get_remaining()) +
            "  |  Mistakes: " + str(self.game.get_mistakes()) +
            "/" + str(GameState.MAX_MISTAKES) +
            "  |  Score: " + str(self.game.get_score()) 
        )

    def end_round(self, reason):
        gs = self.game

        if reason == "win":
            self.status.set("All 5 differences found!")
            messagebox.showinfo(
                "You Win!",
                "Excellent! You found all 5 differences!\nScore: " + str(gs.get_score()), parent = self.root
            )
        else:
            self.status.set(
                "Too many mistakes! Found " +
                str(len(gs.get_found())) + "/5 — Load a new image to play again."
            )
            messagebox.showinfo(
                "Game Over",
                "You made 3 mistakes.\nFound: " + str(len(gs.get_found())) +
                "/5  |  Score: " + str(gs.get_score()), parent = self.root
            )



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

        self.refresh_info()
        

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
            messagebox.showerror('Image canot be Loaded', str(ex),parent=self.root)
            return
        
        self.status.set('')
        self.render_frame()
        
    def reveal_all(self):
        if not self.game:
            messagebox.showwarning('Start Game','Load an image first', parent=self.root)
            return
        r = 32
        for x, y in self.game.get_processor().get_difference_centres():
            if (x, y) not in self.game.get_found():
                for frame in (self.frame_left, self.frame_right):
                    frame.create_oval(
                        x - r, y - r, x + r, y + r,
                        outline="#4ade80", width=3
                    )
        self.status.set("All differences revealed. Load a new image to play again.")

    def restart(self):
        if not self.game:
            messagebox.showwarning("No Game", "Please load an image first.", parent=self.root)
            return
        path = self.game.get_processor().get_path()
        try:
            processor = ImageProcessor(path)
            self.game = GameState(processor)
        except (FileNotFoundError, RuntimeError) as exc: 
            messagebox.showerror("Error", str(exc), parent=self.root)
            return
        self.status.set("")
        self.render_frame()
    



# main function call
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()