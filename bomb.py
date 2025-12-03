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
# generates the bootup sequence on the LCD
def bootup(n=0):
    # show the boot text
    gui._lscroll["text"] = boot_text.replace("\x00", "")
    # after 2 seconds, start the trivia sequence
    gui.after(2000, start_bomb_sequence)

def display_on_lcd(text):
    """
    Show text on the scrolling LCD area.
    Right now we just use the boot/scroll label.
    """
    gui._lscroll["text"] = text

def get_keypad_input():
    """
    Read a string from the physical keypad on the RPi.
    - Digits 0–9 are appended to the current input.
    - '#' = submit/enter.
    - '*' = clear current input.
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
                    # submit answer
                    return value
                elif key == "*":
                    # clear input
                    value = ""
                    display_on_lcd(value)
                else:
                    # append digit and show it
                    value += key
                    display_on_lcd(value)
            sleep(0.1)
    else:
        # fallback for testing on a non-RPi machine
        return input("Enter answer: ")

###########
# trivia / math question phase
###########

# total seconds removed from the bomb timer due to wrong answers
time_penalty = 0

def start_bomb_sequence():
    """
    Ask each math trivia question in order.
    - User must answer correctly to move on.
    - Wrong answer: subtract TRIVIA_PENALTY seconds from the bomb timer.
    After all questions are correct, start the regular bomb phases.
    """
    global time_penalty

    for q in trivia_questions:
        # show the current question
        display_on_lcd(q["question"])

        while True:
            user_input = get_keypad_input()
            if user_input is None:
                user_input = ""
            user_input = user_input.strip()

            if user_input == q["answer"]:
                # correct
                display_on_lcd("Correct!")
                sleep(1)
                break  # move to next question
            else:
                # incorrect -> penalty
                time_penalty += TRIVIA_PENALTY
                display_on_lcd(f"Incorrect! -{TRIVIA_PENALTY}s")
                sleep(1)
                # re-show the question
                display_on_lcd(q["question"])

    # all questions done correctly -> start the bomb
    gui.setup()
    if (RPi):
        setup_phases()
        check_phases()

###########
# phase/thread setup and checking (your original logic, slightly tweaked)
###########

# sets up the phase threads
def setup_phases():
    global timer, keypad, wires, button, toggles, time_penalty
    
    # apply trivia time penalty to the starting timer value
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
    timer._running = False
    keypad._running = False
    wires._running = False
    button._running = False
    toggles._running = False

    # turn off the 7-segment display
    component_7seg.blink_rate = 0
    component_7seg.fill(0)
    # turn off the pushbutton's LED
    for pin in button._rgb:
        pin.value = True

###### 
# MAIN
######

# initialize the LCD GUI
window = Tk()
gui = Lcd(window)

# initialize the bomb strikes and active phases (i.e., not yet defused)
strikes_left = NUM_STRIKES
active_phases = NUM_PHASES

# "boot" the bomb (bootup will call start_bomb_sequence afterwards)
gui.after(100, bootup)

# display the LCD GUI
window.mainloop()
