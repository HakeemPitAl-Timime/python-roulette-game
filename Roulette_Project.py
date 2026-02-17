"""Yuhan Peter Bauer, Zephyr Bégin Zhang, and Hakeem Pit Al-Timime"""

import tkinter as tk
from tkinter import messagebox
import math
import random 

# ------------------------------ Configuration & Helpers ------------------------------

EUROPEAN_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23,
    10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
]  # clockwise

#Which numbers associate with which number
RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = set(range(1, 37)) - RED_NUMBERS
SECTOR_ANGLE = 2 * math.pi / (len(BLACK_NUMBERS) + len(RED_NUMBERS)+1)  # radians per sector

#Colour Choices
DARK_GREEN = "#01431E"
GREEN = '#016D29'
RED = '#E0080B'
BLACK = '#000000'

#Font
BASE_FONT = ("Comfortaa", 12, "bold")
def number_color(n):
    if n == 0:
        return GREEN
    return RED if n in RED_NUMBERS else BLACK

# ------------------------------ Wheel Canvas ------------------------------

class WheelCanvas(tk.Canvas):
    """Canvas subclass that draws the roulette wheel and animates the spin.
    Handles angles, physics simulation, ball movement, and winner detection.
    """
    def __init__(self, parent, radius=140, **kwargs):
        # Create a wheel canvas to fit the wheel
        super().__init__(parent, width=2*(radius+30), height=2*(radius+30), bg=DARK_GREEN, highlightthickness=0, **kwargs)

        self.update_idletasks()
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
                
        self.radius = radius
        self.center = (self.winfo_reqwidth()//2, self.winfo_reqheight()//2)

        #ADDED FOR HIGHLIGHT_WINNER METHOD
        self.highlight_id = None

        self.wheel_angle = 0.0              # rotation of wheel (radians)
        self.ball_angle = 0.0               # current ball angle (radians)
        self.wheel_vel = 0.0                # wheel angular velocity
        self.ball_vel = 0.0                 # ball angular velocity
        self.wheel_decel = 0.0              # wheel angular decel
        self.ball_decel = 0.0               # ball angular decel
        self.isAnimating = False
        self.items = {}

        self.draw_static()

        # self.bind('<Button-1>', self.spin_wheel(self.highlight_winner))  # Left click to spin?
        
    # Draw the wheel. Everything is static, updates make it look dynamic
    def draw_static(self):
        self.delete("all")
        cx, cy = self.center
        R = self.radius
        # Outer ring of the table
        self.create_oval(cx-R-20, cy-R-20, cx+R+20, cy+R+20, fill="#3C1912", outline="")
         
        # Number ring (sectors)
        for indx, n in enumerate(EUROPEAN_ORDER):
            a0 = indx * SECTOR_ANGLE + self.wheel_angle
            a1 = a0 + SECTOR_ANGLE
            # draw sector as a wedge polygon
            p0 = (cx, cy)
            r1 = R
            x1, y1 = cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)
            x2, y2 = cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)
            
            col = number_color(n)   # Set color based on number 
            # Creates a triangle sector for each number
            self.create_polygon(p0[0], p0[1], x1, y1, x2, y2, fill=col, outline="#111")

        # Alternative method to create sectors, but colors are messed up
        # if you want to use it, fix the color assignment part
        """
        for idx, n in enumerate(EUROPEAN_ORDER):
            start_angle = idx * SECTOR_ANGLE + self.wheel_angle
            col = number_color(n)   # Set color based on number
            
            # Convert angles from radians to degrees (create_arc uses degrees)
            start_angle_deg = math.degrees(start_angle)
            extent_angle_deg = math.degrees(SECTOR_ANGLE)
            
            # Draw sector as a pie slice
            self.create_arc(
                cx - R, cy - R,      # Top-left bounding box
                cx + R, cy + R,      # Bottom-right bounding box 
                start=start_angle_deg,
                extent=extent_angle_deg,
                fill=col,
                outline="#111",
                style=tk.PIESLICE    # This creates the wedge shape
            )
        """
        
        # Number labels
        for idx, n in enumerate(EUROPEAN_ORDER):
            a = (idx + 0.5) * SECTOR_ANGLE + self.wheel_angle
            r_text = R - 15 # Set text radius so it's placed inside visible part of triangle
            x, y = cx + r_text * math.cos(a), cy + r_text * math.sin(a)
            self.create_text(x, y, text=str(n), fill="white", font=BASE_FONT)
        
        # Inner circle to cover triangle tips
        self.create_oval(cx-R+45, cy-R+45, cx+R-45, cy+R-45, fill="#222", outline="#111")

        # Create ball and give id
        # The ball is drawn on edge as to not overlap with numbers
        # Otherwise it would be hard to see
        r_to_ball = R - 35 # Ball distance from center of wheel
        BALL_RADIUS = 6
        bx = cx + r_to_ball * math.cos(self.ball_angle)
        by = cy + r_to_ball * math.sin(self.ball_angle)
        self.items["ball"] = self.create_oval(bx-BALL_RADIUS, by-BALL_RADIUS, bx+BALL_RADIUS, by+BALL_RADIUS, fill="white", outline="black", width=1)

    # Set initial angles of wheel and ball, used for testing
    '''
    def set_angles(self, wheel_angle, ball_angle):
        self.wheel_angle = wheel_angle
        self.ball_angle = ball_angle
        self.draw_static()
    '''
    # on_done is the callback function when spin is done
    # This function animates the wheel and ball spinning and decelerating
    # Handles the main animation loop of the wheel
    def spin_wheel(self, on_done):
        if self.isAnimating: return # prevent multiple spins at once
        self.isAnimating = True
        
        # Randomize initial velocities and decelerations
        # Have spin be in opposite directions
        self.wheel_vel = 5 + random.random() * 2 # radians per frame
        self.ball_vel = -10 - random.random() * 4  # radians per frame, make ball faster than wheel
        self.wheel_decel = 0.04 + random.random() * 0.02    # decel has to be pos.
        self.ball_decel = 0.08 + random.random() * 0.03     # decel has to be pos.

        # Helper fuction to update the animation
        def update():
            if not self.isAnimating: return # Prevent updates if animation stopped
            
            def decel(vel, decel):
                # Decelerate velocity towards zero
                # This part is for the wheel
                if vel > 0:
                    vel = max(0, vel - decel)   # prevent neg. velocity
                # This part is for the ball
                else:
                    vel = min(0, vel + decel)   # increase vel. towards 0
                return vel
            
            self.wheel_vel = decel(self.wheel_vel, self.wheel_decel)
            self.ball_vel = decel(self.ball_vel, self.ball_decel)
            
            # Update angles
            self.wheel_angle = (self.wheel_angle + self.wheel_vel * 0.03) % (2 * math.pi)   # Mult is for smoother animation
            self.ball_angle = (self.ball_angle + self.ball_vel * 0.03) % (2 * math.pi)
            self.draw_static()
            
            # Check if both have stopped to end animation
            if abs(self.wheel_vel) < 0.01 and abs(self.ball_vel) < 0.01:
                self.isAnimating = False
                
                # determine winner
                winner = self._resolve_winner()
                self.highlight_winner(winner)
                on_done(winner)
            else:
                self.after(30, update)  # schedule next update in 20 ms
                
        update()
    
    def _resolve_winner(self):
        """
        Determine winning number from relative angle of ball vs wheel.
        Interpret the ball angle in the frame of the wheel.
        """
        # relative angle: where the ball is over the numbered ring after accounting for wheel rotation
        # Use this to compare radians with the sectors to match
        rel_angle = (self.ball_angle - self.wheel_angle) % (2 * math.pi)
        # sector index
        idx = round(rel_angle // SECTOR_ANGLE) % len(EUROPEAN_ORDER)
        return EUROPEAN_ORDER[idx]

    def highlight_winner(self, num):
        if self.highlight_id is not None:
            self.delete(self.highlight_id)
            self.highlight_id = None

        cx, cy = self.center
        R = self.radius
        idx = EUROPEAN_ORDER.index(num)
        a0 = idx * SECTOR_ANGLE + self.wheel_angle
        a1 = a0 + SECTOR_ANGLE
        x1, y1 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        x2, y2 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        self.create_polygon(cx, cy, x1, y1, x2, y2, fill="", outline="yellow", width=3)
        self.highlight_id = self.create_polygon(
            cx, cy, x1, y1, x2, y2,
            fill="", outline="yellow", width=3
    )
    #HIGHLIGHT_ID ADDED B/C PREVENT MULTIPLE OVERLAPPNG HIGHLIGHTS 


# ------------------------------ Betting Table Canvas ------------------------------

class TableCanvas(tk.Canvas):
    """Canvas for displaying the roulette betting table.
    Draws the betting layout and handles bet placements.
    Vertical placement"""
    
    
    CELL_W, CELL_H = 60, 40   # cell size
    
        # Real casino horizontal layout (3 rows, 12 columns)
    ROW1 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
    ROW2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
    ROW3 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
    
    def __init__(self, parent, width, height, chip_getter, **kwargs):
        super().__init__(parent, width=width+20, height=height, bg=DARK_GREEN, highlightthickness=0, **kwargs)
        self.chip_getter = chip_getter  # Function to get current chip value
        self.cell_map = {}  # Map of cell coordinates to bet types.     cell_id -> bet_id   bet_id is split in bet type and it's value
        self.bets = {}  # Dictionary to store bets placed.              bet_id -> amount
        self.drawn_chips = {}  # Map of cell_id to chip item on canvas  bet_id -> chip, text

        self._draw_table()
    
    # This function draws a single cell in the betting table
    # Modified to support text angle for vertical text on later half of the table
    def _draw_cell(self, x0, y0, x1, y1, text, fill, bet_id, text_color="white", angle=0):
        # Creates the rectangle cell for betting
        # and add it's mapping to cell_map
        cell = self.create_rectangle(x0, y0, x1, y1, fill=fill, outline="white", width=2)        
        self.cell_map[cell] = bet_id
        
        # Calculate text position and create text
        textx, texty = (x0 + x1)//2, (y0 + y1)//2
        self.create_text(textx, texty, text=text, fill=text_color, 
                        font=BASE_FONT, angle=angle)
        return cell
    
    # This function draws the entire betting table layout
    def _draw_table(self):
        self.delete("all")
        
        pad_x, pad_y = 10, 10
        cell_w, cell_h = TableCanvas.CELL_W, TableCanvas.CELL_H   # cell size
        
        y_offset = self.winfo_reqheight()//2 - (pad_y + cell_h*7)   # Helps center the table vertically
        
        # Draw 0 cells separately
        zero = self._draw_cell(pad_x, pad_y + y_offset, pad_x + cell_w*3, pad_y + cell_h + y_offset,
                               "0", GREEN, ("number", 0))
        # Numbers grid (1..36) in 12 rows (top to bottom), 3 columns (left to right: 1st column is "1,4,7,...")
        # Creating from left to right, top to bottom
        
        start_x = pad_x                         # start position from where to draw table
        start_y = pad_y + cell_h + y_offset     
        
        # Display numbers from 1-3 to 34-36
        for row in range(12):
            
            row_nums = [(3*row + col) for col in range(1, 4)]
            for col in range(3):
                num = row_nums[col]
                fill = number_color(num)
                text_color = "white"
                
                x0 = start_x + col * cell_w
                y0 = start_y + row * cell_h
                x1 = x0 + cell_w
                y1 = y0 + cell_h
                bet_id = ('number', num)
                self._draw_cell(x0, y0, x1, y1, str(num), fill, bet_id, text_color)
        
        # Create the 2:1 bets cells row
        for col in range(3):
            x0 = start_x + col * cell_w
            y0 = start_y + 12 * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            text = "2 to 1"
            fill = GREEN
            bet_id = ('column', col+1)
            self._draw_cell(x0, y0, x1, y1, text, fill, bet_id, text_color)
            
        # Create the Dozens column;
        dozens = ["1st 12", "2nd 12", "3rd 12"]
        for row in range(3):
            x0 = start_x + 3 * cell_w
            y0 = start_y + 4*row * cell_h
            x1 = x0 + cell_w*0.5
            y1 = y0 + 4*cell_h
            
            text = dozens[row]
            fill = GREEN
            bet_id = ('dozen', row+1)
            # Angle set to 90 degrees for vertical text
            self._draw_cell(x0, y0, x1, y1, text, fill, bet_id, text_color, angle=90)
        
        # Add final colun for Even, Red, Low, etc.
        texts = ["1 to 18", "EVEN", "RED", "BLACK", "ODD", "19 to 36"]
        bet_ids = ['range', 'parity', 'color', 'color', 'parity', 'range']
        for row in range(6):
            x0 = start_x + 3.5 * cell_w
            y0 = start_y + row * 2 * cell_h
            x1 = x0 + cell_w*0.5
            y1 = y0 + 2*cell_h
            
            text = texts[row]
            bet_id = (bet_ids[row], texts[row])  # e.g., ('color', 'RED')
            
            if text == "RED" or text == "BLACK":
                fill = RED if text == "RED" else BLACK
            else: 
                fill = GREEN
            text_color = "white"
            
            # Angle set to 90 degrees for vertical text
            self._draw_cell(x0, y0, x1, y1, text, fill, bet_id, text_color, angle=90)
    
        self.bind("<Button-1>", self._on_click) # Bind click event to place bets
        
    # Draw or update chip on the given cell    
    def _draw_chip(self, cell_id, bet_id):
        x1, y1, x2, y2 = self.coords(cell_id)   # get cell coords
        cx, cy = (x1+x2)/2, (y1+y2)/2           # center of cell
        amt = self.bets[bet_id]

        if bet_id in self.drawn_chips: # Update existing chip
            cell_item, text_item = self.drawn_chips[bet_id]     # Get existing bet and text items
            self.coords(cell_item, cx-14, cy-14, cx+14, cy+14)  # Move chip to center
            self.itemconfig(text_item, text=str(amt))           # Update text displayed on screen
            self.coords(text_item, cx, cy)                      # Move text to center of chip
        else:                           # Create new chip
            chip = self.create_oval(cx-14, cy-14, cx+14, cy+14, # Create chip oval
                                 fill="gold", outline="black")  
            text = self.create_text(cx, cy, text=str(amt),      # Create associated text amount
                                 font=("Arial", 9, "bold"))
            self.drawn_chips[bet_id] = (chip, text)             # Add chip to drawn_chips map
    
    # Handle click events to place bets
    def _on_click(self, event):
        items = self.find_overlapping(event.x, event.y, event.x, event.y)   # Fund clicked cell and items
                                                                            # Start and end of event size box are the same because
                                                                            # click is a point
        for item in items:
            if item in self.cell_map:               # Check if clicked item is a cell
                bet_id = self.cell_map[item]        # Get bet_id from cell_map
                chip = self.chip_getter()           # Get current chip value from chip_getter function
                if chip > 0:
                    self.bets[bet_id] = self.bets.get(bet_id, 0) + chip  # Update bets dictionary
                    self._draw_chip(item, bet_id)                        # Draw or update chip on the cell
                return
    
    # Getter for bets dictionary   
    def get_bets(self):
        return self.bets            
    
    def clear_bets(self):
        self.bets.clear()
        self.drawn_chips.clear()
        self._draw_table()  # Redraw table to clear chips
        
# ------------------------------ Main Runner ------------------------------

class Roulette(tk.Tk):
    """Main application class that builds the roulette game window, connects all components,
    manages the player's balance, chip selection, wheel spins, bet validation, and payout handling.
    This class uses the WheelCanvas, TableCanvas, and user interface controls."""

    def __init__(self):
        # Create main window
        super().__init__()
        self.title("Roulette Game")
        self.configure(bg=DARK_GREEN)
        
        # Set default padding for all widgets
        PADX = 20
        PADY = 20
        
        # Set window dimensions
        # Get user screen dimensions and create screen-centered window
        SCREEN_WIDTH = self.winfo_screenwidth()
        SCREEN_HEIGHT = self.winfo_screenheight()
        
        TABLE_WINDOW_WIDTH = TableCanvas.CELL_W*4
        TABLE_WINDOW_HEIGHT = 14*TableCanvas.CELL_H + 2*PADY
        
        WINDOW_WIDTH = 770      # Arbitrary value that fits both canvases
        WINDOW_HEIGHT = 800     # Arbitrary value that fits both canvases
        
        x_pos = (SCREEN_WIDTH // 2) - (WINDOW_WIDTH // 2)       # Find center x position
        y_pos = (SCREEN_HEIGHT//2) - (WINDOW_HEIGHT//2)  # Find center y position
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_pos}+{y_pos}")  # Set window size and position
        self.resizable(False, False)        # Disable window resizing
        
        # Create game state variables
        self.balance = 2000  # Starting balance for the player
        self.current_chip = tk.IntVar(value=100)  # Current bet amount
        self.isSpinning = False  # Flag to check if the wheel is spinning
        
        # Create and place Wheel and Table canvase
        self.wheel = WheelCanvas(self, radius=200)
        self.wheel.grid(row=0, column=0, padx=PADX, pady=PADY)
        
        self.table = TableCanvas(self, width=TABLE_WINDOW_WIDTH,
                                 height=TABLE_WINDOW_HEIGHT, chip_getter=lambda: self.current_chip.get()) 
        self.table.grid(row=0, column=1, pady=10)
        
        # Create control pannel below canvases
        self._build_controls()
        self.controls_frame.grid(row=2, column=0, columnspan=2)
        
        # Result label
        self.result_var = tk.StringVar(value="Place your bets.")    # Use a StringVar for dynamic text updates
                                                                    # instead of static label text
        self.result_lbl = tk.Label(self, textvariable=self.result_var,
                                   font=BASE_FONT,
                                   bg=DARK_GREEN, fg="white")
        self.result_lbl.grid(row=3, column=0, columnspan=2, pady=5)
        
        print('Window width:', WINDOW_WIDTH, 'Window height:', WINDOW_HEIGHT)
        print('Wheel width:', self.wheel.width, 'Wheel height:', self.wheel.height)
        print(f'table width: {SCREEN_WIDTH - self.wheel.width}', f'table height: {SCREEN_HEIGHT - 4*PADY}')
        
    # Create the control pannel frame for buttons and labels accessible by user
    def _build_controls(self):
        # create fram for control pannel of buttons and labels
        self.controls_frame = tk.Frame(self, bg="#3C1912")

        # Create chip selection radio buttons
        tk.Label(self.controls_frame, text="Chip:",
                 bg="#3C1912", fg="white").grid(row=0, column=0, padx=5)

        # Radio buttons for chip selection are a good choice since only one can be selected at a time
        for j, val in enumerate([1,5,25,100,500, 1000]): 
            tk.Radiobutton(self.controls_frame, text=str(val),
                           value=val, variable=self.current_chip,
                           bg="#3C1912", fg="white", selectcolor="#333"
                           ).grid(row=0, column=1+j, padx=3)
            
        # Spin button
        tk.Button(self.controls_frame, text="Spin",
                  command=self.on_spin, bg=GREEN, fg="white",
                  font=BASE_FONT,
                  width=10).grid(row=0, column=8, padx=15, pady=5)
        
        # Clear bets button
        tk.Button(self.controls_frame, text="Clear Bets",
                  command=self.on_clear, bg=RED, fg="white",
                  font=BASE_FONT
                  ).grid(row=0, column=9, padx=5, pady=5)
    
        # Balance label - Display current balance
        self.balance_var = tk.StringVar()
        tk.Label(self.controls_frame, textvariable=self.balance_var,
                 bg="#3C1912", fg="white",
                 font=BASE_FONT
                 ).grid(row=0, column=10, padx=20)
        self._update_balance_label()
        
    def _update_balance_label(self):
        self.balance_var.set(f"Balance: ${self.balance}")
    
    # Compuutes payout of bet based on european roulette rules
    def _compute_payout(self, bets, winning_number):
        payout = 0
        for (bet_type, val), amount in bets.items():
            # We don't return after the checks because a bet can cover multiple conditions
            # Or the user could have placed multiple bets on different bet types            
            if bet_type == 'number':
                if val == winning_number:
                    payout += amount * 36
                
            elif bet_type == 'color':
                if (val == 'RED' and winning_number in RED_NUMBERS) or \
                   (val == 'BLACK' and winning_number in BLACK_NUMBERS):
                    payout += amount * 2
            
            elif bet_type == 'parity':
                if (val == 'EVEN' and winning_number != 0 and winning_number % 2 == 0) or \
                   (val == 'ODD' and winning_number % 2 == 1):
                    payout += amount * 2
            
            elif bet_type == 'range':
                if (val == '1 to 18' and 1 <= winning_number <= 18) or \
                   (val == '19 to 36' and 19 <= winning_number <= 36):
                   payout += amount * 2
            
            elif bet_type == 'dozen':
                if (val == 1 and 1 <= winning_number <= 12) or \
                   (val == 2 and 13 <= winning_number <= 24) or \
                   (val == 3 and 25 <= winning_number <= 36):
                    payout += amount * 3
            
            elif bet_type == 'column':
                if (val == 1 and winning_number in TableCanvas.ROW1) or \
                   (val == 2 and winning_number in TableCanvas.ROW2) or \
                   (val == 3 and winning_number in TableCanvas.ROW3):
                    payout += amount * 3
                    
            return payout
    
    def _on_lose(self):
        self.result_var.set("Oh no! You're BROKE! Game over.")
        if messagebox.askyesno("Game Over", "You're out of money! The casino wins!\nDo you want to quit?"):
            self.destroy()
       
    # Handles operations after the wheel spin is complete
    # such as computing payout and updating balance before next round
    def _after_spin(self, win):
        bets = self.table.get_bets()
        payout = self._compute_payout(bets, win)
        
        self.balance += payout  # Add payout to balance
        self._update_balance_label()
        
        # Update result label to display winning number and payout
        color = 'RED' if number_color(win) == RED else 'BLACK' if number_color(win) == BLACK else 'GREEN'
        if payout > 0:
            self.result_var.set(f"Result: {win} ({color}) - You won ${payout}!")
        elif self.balance == 0:
            self._on_lose()
        else:
            self.result_var.set(f"Result: {win} ({color}) - You lost. Better luck next time!")
        
        self.isSpinning = False
    
    # Clear bets button handler
    def on_clear(self):
        if self.isSpinning: return # Prevent clearing bets while spinning
        self.table.clear_bets()
        if self.balance != 0:
            self.result_var.set("Bets cleared. Place your bets.")
        else: 
            self.result_var.set("You're out of money! Game over.")
            if messagebox.askyesno("Game Over", "You're out of money! The casino wins!\nDo you want to quit?"):
                self.destroy()
    
    # Spin button handler
    def on_spin(self):
        if self.isSpinning: return # Prevent multiple spins at once
        
        bets = self.table.get_bets()
        total_bet = sum(bets.values())
        
        # Validate bets
        if self.balance <= 0:
            if messagebox.askyesno("Game Over", "You're out of money! The casino wins!\nDo you want to quit?"):
                self.destroy()
            return
        if total_bet == 0:
            messagebox.showwarning("No Bets", "Please place at least one bet before spinning.")
            return
        if total_bet > self.balance:
            messagebox.showwarning("Insufficient Balance", "You do not have enough balance to cover your bets.")
            return
        
        # Deduct total bet from balance
        self.balance -= total_bet
        self._update_balance_label()
        
        # Start spinning the wheel
        self.result_var.set("Spinning the wheel...")
        self.isSpinning = True
        # Call spin_wheel with callback to _after_spin
        self.wheel.spin_wheel(on_done=self._after_spin)
        
    
# ------------------------------ Run Application ------------------------------        

if __name__ == "__main__":    
    app = Roulette()
    app.mainloop()

