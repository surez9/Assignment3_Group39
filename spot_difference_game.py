
import tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox



# Load Image in the frame with help of Image Processor
class ImageProcessor:

    IMAGE_SIZE = (450,450)
    def __init__(self,image_path):
        self.path = image_path
        original_image = cv2.imread(image_path)
        
        if original_image is None:
            raise FileNotFoundError("Image not found")
        
        self.original_image = cv2.resize(original_image,self.IMAGE_SIZE)
        

    def get_path(self):
        return self.path
    
    def get_original_image(self):
        return self.original_image.copy()
    


class GameState:

    MAX_MISTAKES = 3

    def __init__(self, processor: ImageProcessor):
        self.processor = processor
    
    def get_processor(self):
        return self.processor



# Main Application Class
class Application:

    FRAME_SIZE = 450

    def __init__(self, root):
        self.root = root
        self.root.title("Spot the Differences")
        self.root.geometry("800x600")
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


    # Image uploader

    def cv_to_tk(self,img):
        return ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

    def render_frame(self):
        original_image = self.cv_to_tk(self.game.get_processor().get_original_image())

        self.frame_left.delete('all')
        self.frame_left.create_image(0,0,anchor="nw",image=original_image)
        self.frame_left.photo = original_image

        
        

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