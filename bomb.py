#################################
# CSC 102 Defuse the Bomb Project
# Main program
# Team: 
#################################

# import the configs
from bomb_configs import *
# import the phases
from bomb_phases import *

# tkinter helpers for modal dialogs
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as messagebox

###########
# functions
###########
# generates the bootup sequence on the LCD
def bootup(n=0):
    gui._lscroll["text"] = boot_text.replace("\x00", "")
    # configure the remaining GUI widgets
    gui.setup()
    # setup the phase threads, execute them, and check their statuses
    if (RPi):
        setup_phases()
        # If running on the Pi, you can enable the question flow here as well:
        present_math_questions()
        # continue normal phase checking loop
        check_phases()
    else:
        # For local development (RPi == False) run the math questions so you can test dialogs
        present_math_questions()
        # If you want the rest of the phase-check loop for dev, you can call check_phases() here as well
    # if we're animating
   

# presents simple math questions one-by-one using modal dialogs
# first question: 2+2 -> if correct go to question 2
def present_math_questions():
    global strikes_left
    # List of (prompt, expected_answer) tuples.
    questions = [
        ("What is 2 + 2?", "4"),
        ("Question 2: What is 3 + 4?", "7"),
    ]

    for idx, (prompt, expected) in enumerate(questions):
        # keep asking until correct or out of strikes
        while True:
            answer = simpledialog.askstring(f"Math Question {idx+1}", prompt, parent=window)
            if answer is None:
                # treat cancel as incorrect attempt
                strikes_left -= 1
                messagebox.showinfo("Incorrect", f"No answer provided. Strike! Strikes left: {strikes_left}", parent=window)
            else:
                if answer.strip() == expected:
                    messagebox.showinfo("Correct", "Correct! Moving to the next question.", parent=window)
                    break
                else:
                    strikes_left -= 1
                    messagebox.showinfo("Incorrect", f"Wrong answer. Strike! Strikes left: {strikes_left}", parent=window)

            # if out of strikes, explode and stop asking
            if strikes_left <= 0:
                turn_off()
                gui.after(100, gui.conclusion, False)
                return

# sets up the phase threads
def setup_phases():
    global timer, keypad, wires, button, toggles
    
    # setup the timer thread
    timer = Timer(component_7seg, COUNTDOWN)
    # bind the 7-segment display to the LCD GUI so that it can be paused/unpaused from the GUI
    gui.setTimer(timer)
    # setup the keypad thread
    keypad = Keypad(component_keypad, keypad_target)
    # setup the jumper wires thread
    wires = Wires(component_wires, wires_target)
    # setup the pushbutton thread
    button = Button(component_button_state, component_button_RGB, button_target, button_color, timer)
    # bind the pushbutton to the LCD GUI so that its LED can be turned off when we quit
    gui.setButton(button)
    # setup the toggle switches thread
    toggles = Toggles(component_toggles, toggles_target)

    # start the phase threads
    timer.start()
    keypad.start()
    wires.start()
    button.start()
    toggles.start()

# checks the phase threads
def check_phases():
    global active_phases
    
    # check the timer
    if (timer._running):
        # update the GUI
        gui._ltimer["text"] = f"Time left: {timer}"
    else:
        # the countdown has expired -> explode!
        # turn off the bomb and render the conclusion GUI
        turn_off()
        gui.after(100, gui.conclusion, False)
        # don't check any more phases
        return
    # check the keypad
    if (keypad._running):
        # update the GUI
        gui._lkeypad["text"] = f"Combination: {keypad}"
        # the phase is defused -> stop the thread
        if (keypad._defused):
            keypad._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (keypad._failed):
            strike()
            # reset the keypad
            keypad._failed = False
            keypad._value = ""
    # check the wires
    if (wires._running):
        # update the GUI
        gui._lwires["text"] = f"Wires: {wires}"
        # the phase is defused -> stop the thread
        if (wires._defused):
            wires._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (wires._failed):
            strike()
            # reset the wires
            wires._failed = False
    # check the button
    if (button._running):
        # update the GUI
        gui._lbutton["text"] = f"Button: {button}"
        # the phase is defused -> stop the thread
        if (button._defused):
            button._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (button._failed):
            strike()
            # reset the button
            button._failed = False
    # check the toggles
    if (toggles._running):
        # update the GUI
        gui._ltoggles["text"] = f"Toggles: {toggles}"
        # the phase is defused -> stop the thread
        if (toggles._defused):
            toggles._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (toggles._failed):
            strike()
            # reset the toggles
            toggles._failed = False

    # note the strikes on the GUI
    gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    # too many strikes -> explode!
    if (strikes_left == 0):
        # turn off the bomb and render the conclusion GUI
        turn_off()
        gui.after(1000, gui.conclusion, False)
        # stop checking phases
        return

    # the bomb has been successfully defused!
    if (active_phases == 0):
        # turn off the bomb and render the conclusion GUI
        turn_off()
        gui.after(100, gui.conclusion, True)
        # stop checking phases
        return

    # check the phases again after a slight delay
    gui.after(100, check_phases)

# handles a strike
def strike():
    global strikes_left
    
    # note the strike
    strikes_left -= 1

# turns off the bomb
def turn_off():
    # stop all threads
    try:
        timer._running = False
        keypad._running = False
        wires._running = False
        button._running = False
        toggles._running = False
    except Exception:
        pass

    # turn off the 7-segment display (only if available)
    try:
        component_7seg.blink_rate = 0
        component_7seg.fill(0)
    except Exception:
        pass

    # turn off the pushbutton's LED (only if available)
    try:
        for pin in button._rgb:
            pin.value = True
    except Exception:
        pass

######
# MAIN
######

# initialize the LCD GUI
window = Tk()
gui = Lcd(window)

# initialize the bomb strikes and active phases (i.e., not yet defused)
strikes_left = NUM_STRIKES
active_phases = NUM_PHASES

# "boot" the bomb
gui.after(100, bootup)

# display the LCD GUI
window.mainloop()
