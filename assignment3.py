import cv2
import numpy as Npy
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import random


class Change: #this is the absstract class for all types of changes
    def Applicationly(self, img, x, y):
        raise NotImplementedError

class ColourChange(Change): #we will first convert it from BGR to HSV because in HSV hue/colour has seperate channel 
    def Applicationly(self, img, x, y):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(Npy.int32) #int32 beacuse if we don't do it there will be overflow in addition 
        hsv[y-25:y+25, x-25:x+25, 0] = (hsv[y-25:y+25, x-25:x+25, 0] + 45) % 180 # we will select area 50*50 pixel and add 60 in channel 0 so it will change the colour of that area 
        return cv2.cvtColor(hsv.astype(Npy.uint8), cv2.COLOR_HSV2BGR) # % 180 is used because in openCV the hue is from 0 to 179 and finally we will convert it to BGR

class blur(Change):# Implementation for blurring a region
    def Applicationly(self, img, x, y):
        img[y-25:y+25, x-25:x+25] = cv2.GaussianBlur(img[y-25:y+25, x-25:x+25], (7, 7), 0) #we will blur the image the of 50*50 and blur the image by guassian blur of pixel 7*7
        return img

class imageBrigthness(Change): # Implementation for changing brightness
    def Applicationly(self, img, x, y):
        img[y-25:y+25, x-25:x+25] = cv2.convertScaleAbs(img[y-25:y+25, x-25:x+25], alpha=1.1, beta=50) 
        return img


class processimage: # This class will Handles uploading the image and creating difference
    def __init__(self, path):
        self.orignal = cv2.resize(cv2.imread(path), (410, 410))
        if self.orignal is None:
            raise ValueError("Sorry, Sir your desired image can't be loaded please try again.Thank you!")
        self.modification = self.orignal.copy()
        self.difference = []
        self.make_differnce()

    def make_differnce(self): # This function will Apply randdomly 5 non-overlapping modifications to create difference
        types = [ColourChange(), blur(), imageBrigthness()]
        for _ in range(5):
            # we will find non overlapping difference by checking if the new difference is at least 50 pixels away from all existing ones
            while True:
                x, y = random.randint(40, 360), random.randint(40, 360)
                if all(abs(x - dx) > 50 or abs(y - dy) > 50 for dx, dy in self.difference):
                    break
            self.modification = random.choice(types).Applicationly(self.modification, x, y)
            self.difference.append((x, y))


class Gamelogic:
    def __init__(self):# this class will hangle the logic of game and it's state such as differencefound differences ,incorrect and gamescore
        self.prcessor = None
        self.differencefound = []
        self.incorrect = 0
        self.gamescore = 0  

    def image_load(self, path):
        self.prcessor = processimage(path)
        self.differencefound = []
        self.incorrect = 0
       

    def click(self, x, y): # this will check if it is in 20 pixel radius of any difference and update the gamescore and also respective incorrect
        for dx, dy in self.prcessor.difference:
            if (dx, dy) not in self.differencefound:
                if ((x - dx) ** 2 + (y - dy) ** 2) ** 0.5 <= 20:
                    self.differencefound.append((dx, dy))
                    self.gamescore += 20
                    return True
        self.incorrect += 1 #
        self.gamescore -= 10
        return False


class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Find the difference Game ")
        self.root.geometry("920x600")
        self.root.resizable(False, False)

        self.Gamelogic = Gamelogic()
        self.path = None
        self.locked = False
        self.time_left = 120
        self.time_starts = False

        # left image will shows the orignal image
        self.c_orig = tk.Canvas(root, width=410, height=410, bg="gray")
        self.c_orig.grid(row=0, column=0, padx=10, pady=10)

        # Modified image where the user will click too find the differences 
        self.c_mod = tk.Canvas(root, width=410, height=410, bg="gray")
        self.c_mod.grid(row=0, column=1, padx=10, pady=10)
        self.c_mod.bind("<Button-1>", self.click)

        #we will upload the image by clicking upload image button and the info label will show all the detils such as differences,incorrect, gamescore
        self.info = tk.Label(root, text="Please  load your image to start the game ", font=("Calibri", 12))
        self.info.grid(row=1, column=0, columnspan=2)

        # this code will circle the differences in red circle
        self.status = tk.Label(root, text="", font=("Calibri", 11, "bold"), fg="red")
        self.status.grid(row=2, column=0, columnspan=2)

        # these are some of the control buttons
        tk.Button(root, text="Upload Image", width=15, command=self.image_load).grid(row=3, column=0, pady=8)
        tk.Button(root, text="Reveal Differences",     width=15, command=self.reveal).grid(row=3, column=1, pady=8)
        tk.Button(root, text="Restart Game",    width=15, command=self.restart_game).grid(row=4, column=0, columnspan=2, pady=4)

    # This function will open a file dialog to upload an image, start the Game, and initialize the timer
    def image_load(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
        if not path:
            return
        try:
            self.path = path
            self.Gamelogic.image_load(path)
            self.locked = False
            self.time_left = 120
            self.time_starts = True
            self.status.config(text="")
            self.display()
            self.Tick()
        except Exception as e:
            messagebox.showerror("Error", str(e))

   # In this set of code we will convert the OpenCV image to Tkinter photo image
    def to_tk(self, img):
        return ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

    # This funtion will dispaly the both canvases
    def display(self):
        o = self.to_tk(self.Gamelogic.prcessor.orignal)
        m = self.to_tk(self.Gamelogic.prcessor.modification)

        self.c_orig.delete("all")
        self.c_mod.delete("all")

        self.c_orig.create_image(0, 0, anchor="nw", image=o)
        self.c_orig.image = o  

        self.c_mod.create_image(0, 0, anchor="nw", image=m)
        self.c_mod.image = m

        self._update_info()

    ## Update the info label with remaining differences, incorrect, gamescore, and time
    def _update_info(self):
        remaining = 5 - len(self.Gamelogic.differencefound)
        self.info.config(
            text=f"Remaining: {remaining}  |  incorrect: {self.Gamelogic.incorrect}/3  |  gamescore: {self.Gamelogic.gamescore}  |  Time: {self.time_left}s"
        )

    #  this will count the time if times up it will lock the Game and the user can not procced untill the user restart game or upload a new image
    def Tick(self):
        if self.time_starts and self.Gamelogic.prcessor:
            if self.time_left > 0:
                self.time_left -= 1
                self._update_info()
                self.root.after(1000, self.Tick)
            else:
                self.time_starts = False
                self.locked = True
                self.status.config(text="Your Time is over! please upload a new image to Restart Game.")
                messagebox.showinfo("Your Time Is Over", "Time Up! Game ended.")
     
    def click(self, event):
        if not self.Gamelogic.prcessor or self.locked:
            return

        hit = self.Gamelogic.click(event.x, event.y)

        if hit:
            # if it is correct we wil draw red circles on both images 
            for c in [self.c_orig, self.c_mod]:
                c.create_oval(event.x - 25, event.y - 25,
                              event.x + 25, event.y + 25,
                              outline="red", width=2)
            if len(self.Gamelogic.differencefound) == 5: #if all 5 differences are found the game will end 
                self.time_starts = False
                self.locked = True
                self.status.config(text="All 5 differences are found!")
                messagebox.showinfo("Congrats Mate!", "You found all 5 difference!")
        else:
            if self.Gamelogic.incorrect >= 3: 
                self.time_starts = False
                self.locked = True
                self.status.config(
                    text=f"Too many incorrect! differencefound: {len(self.Gamelogic.differencefound)}/5 — upload a new image to restart game.")
                messagebox.showinfo("Oops Game Over", "You have made 3 wrong clicks — Game Over!")
            else:
                messagebox.showwarning("incorrect!", f"that's not a difference. incorrect: {self.Gamelogic.incorrect}/3")

        self._update_info()

    
    def reveal(self): #This function will reveal all remaining difference by drawing blue circles on both images
        if not self.Gamelogic.prcessor:
            messagebox.showwarning("Warning", "Please upload an image first.")
            return
        self.time_starts = False
        self.locked = True
        for x, y in self.Gamelogic.prcessor.difference:
            if (x, y) not in self.Gamelogic.differencefound:
                for c in [self.c_orig, self.c_mod]:
                    c.create_oval(x - 30, y - 30, x + 30, y + 30,
                                  outline="blue", width=2) #we will draw blue circle to reavel the differences from in both images
        self.status.config(text="All difference revealed. please upload a new image to play again.")

    
    def restart_game(self):  # restart game Gamelogic with differnent changes on the same image
        if not self.path:
            messagebox.showwarning("Warning", "oops please load your image first")
            return
        self.Gamelogic.image_load(self.path)
        self.locked = False
        self.time_left = 120
        self.time_starts = True
        self.status.config(text="")
        self.display()
        self.Tick()



root = tk.Tk()
Application(root)
root.mainloop()
