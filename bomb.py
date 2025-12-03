#################################
# CSC 102 Defuse the Bomb Project
# Main program
# Team: 
#################################

# import the configs
from bomb_configs import *
# import the phases
from bomb_phases import *

from time import sleep

###########
# helper functions
###########

def display_on_lcd(text):
    """Show text on the scrolling LCD area."""
    gui._lscroll["text"] = text

def get_keypad_input():
    """
    Read a string from the physical keypad on the RPi.
    Digits -> build the input
    '*'    -> clear
    '#'    -> submit
    """
    if RPi:
        value = ""
        display_on_lcd(value)
        while True:
            if component_keypad.pressed_keys:
                key = str(component_keypad.pressed_keys[0])

                # debounce
                while component_keypad.pressed_keys:
                    sleep(0.1)

                if key == "#":
                    return value
                elif key == "*":
                    value = ""
                    display_on_lcd(value)
                else:
                    value += key
                    display_on_lcd(value)
            sleep(0.1)
    else:
        return input("Enter answer: ")

###########
# functions
###########

# total seconds removed from the bomb timer due to wrong answers
time_penalty = 0

# generates the bootup sequence on the LCD
def bootup(n=0):
    # show the boot text
    gui._lscroll["text"] = boot_text.replace("\x00", "")
    # AFTER boot, start the trivia sequence
    gui.after(2000, start_bomb_sequence)

def start_bomb_sequence():
    """
    Ask each math trivia question in order.
    Wrong answer: subtract TRIVIA_PENALTY seconds from the timer.
    After all correct, start the regular bomb phases.
    """
    global time_penalty

    for q in trivia_questions:
        display_on_lcd(q["question"])

        while True:
            user_input = get_keypad_input()
            if user_input is None:
                user_input = ""
            user_input = user_input.strip()

            if user_input == q["answer"]:
                display_on_lcd("Correct!")
                sleep(1)
                break
            else:
                time_penalty += TRIVIA_PENALTY
                display_on_lcd(f"Incorrect! -{TRIVIA_PENALTY}s")
                sleep(1)
                display_on_lcd(q["question"])

    # all questions done correctly -> now configure and start the bomb
    gui.setup()
    if (RPi):
        setup_phases()
        check_phases()

# sets up the phase threads
def setup_phases():
    global timer, keypad, wires, button, toggles, time_penalty
    
    # apply trivia time penalty
    start_value = max(0, COUNTDOWN - time_penalty)

    # setup the timer thread
    timer = Timer(component_7seg, start_value)
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

# checks the phase threads (unchanged from your original)
def check_phases():
    global active_phases
    
    # check the timer
    if (timer._running):
        gui._ltimer["text"] = f"Time left: {timer}"
    else:
        turn_off()
        gui.after(100, gui.conclusion, False)
        return

    # check the keypad
    if (keypad._running):
        gui._lkeypad["text"] = f"Combination: {keypad}"
        if (keypad._defused):
            keypad._running = False
            active_phases -= 1
        elif (keypad._failed):
            strike()
            keypad._failed = False
            keypad._value = ""

    # check the wires
    if (wires._running):
        gui._lwires["text"] = f"Wires: {wires}"
        if (wires._defused):
            wires._running = False
            active_phases -= 1
        elif (wires._failed):
            strike()
            wires._failed = False

    # check the button
    if (button._running):
        gui._lbutton["text"] = f"Button: {button}"
        if (button._defused):
            button._running = False
            active_phases -= 1
        elif (button._failed):
            strike()
            button._failed = False

    # check the toggles
    if (toggles._running):
        gui._ltoggles["text"] = f"Toggles: {toggles}"
        if (toggles._defused):
            toggles._running = False
            active_phases -= 1
        elif (toggles._failed):
            strike()
            toggles._failed = False

    gui._lstrikes["text"] = f"Strikes left: {strikes_left}"

    if (strikes_left == 0):
        turn_off()
        gui.after(1000, gui.conclusion, False)
        return

    if (active_phases == 0):
        turn_off()
        gui.after(100, gui.conclusion, True)
        return

    gui.after(100, check_phases)

# handles a strike
def strike():
    global strikes_left
    strikes_left -= 1

# turns off the bomb
def turn_off():
    timer._running = False
    keypad._running = False
    wires._running = False
    button._running = False
    toggles._running = False

    component_7seg.blink_rate = 0
    component_7seg.fill(0)
    for pin in button._rgb:
        pin.value = True

###### 
# MAIN
######

window = Tk()
gui = Lcd(window)

strikes_left = NUM_STRIKES
active_phases = NUM_PHASES

# bootup will now ALSO start the trivia after showing text
gui.after(100, bootup)

window.mainloop()
