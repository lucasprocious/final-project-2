#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions
# Team: 
#################################

# import the configs
from bomb_configs import *
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
import os
import sys

#########
# classes
#########
# the LCD display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        window.attributes("-fullscreen", True)

        self._timer = None     # (will be set later)
        self._button = None    # (will be set later)

        self.setupBoot()

    # ----------------------------------------------------
    # BOOT SCREEN: Shows boot text + first trivia question
    # ----------------------------------------------------
    def setupBoot(self):
        from bomb_configs import boot_text, trivia_questions

        # Layout spacing
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)

        # Show scrolling boot text
        self._lscroll = Label(
            self, bg="black", fg="white",
            font=("Courier New", 14),
            text=boot_text,
            justify=LEFT
        )
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W)

        # Trivia Question
        self._lquestion = Label(
            self, bg="black", fg="cyan",
            font=("Courier New", 18),
            text=trivia_questions[0]['question']
        )
        self._lquestion.grid(row=1, column=0, columnspan=3, pady=20)

        # User input box
        self._answer_entry = Entry(self, font=("Courier New", 18))
        self._answer_entry.grid(row=2, column=0, columnspan=3)

        # Submit button
        self._submit_button = Button(
            self, text="Submit",
            bg="red", fg="white",
            font=("Courier New", 18),
            command=self.checkTriviaAnswer
        )
        self._submit_button.grid(row=3, column=1, pady=20)

        # Tracks question index (you have 2 trivia questions)
        self.current_question_index = 0

        self.pack(fill=BOTH, expand=True)

    # ----------------------------------------------------
    # CHECK TRIVIA ANSWER: Runs when user clicks "Submit"
    # ----------------------------------------------------
    def checkTriviaAnswer(self):
        from bomb_configs import trivia_questions, TRIVIA_PENALTY
        global timer

        user = self._answer_entry.get()
        correct = trivia_questions[self.current_question_index]['answer']

        # Correct answer
        if user == correct:
            self.current_question_index += 1

            # More questions?
            if self.current_question_index < len(trivia_questions):
                self._lquestion['text'] = trivia_questions[self.current_question_index]['question']
                self._answer_entry.delete(0, END)
            else:
                self.startBomb()   # ALL QUESTIONS DONE → start bomb

        # Wrong answer
        else:
            self._lquestion['text'] = f"Incorrect! Try again."
            self._answer_entry.delete(0, END)

    # ----------------------------------------------------
    # START THE ACTUAL BOMB (timer, phases, GUI)
    # ----------------------------------------------------
    def startBomb(self):
        # Remove boot UI widgets
        self._lscroll.destroy()
        self._lquestion.destroy()
        self._answer_entry.destroy()
        self._submit_button.destroy()

        # Load main bomb GUI
        self.setup()

        # Start real bomb phases
        from bomb_configs import RPi
        if RPi:
            setup_phases()
            check_phases()

    # ----------------------------------------------------
    # MAIN BOMB GUI (unchanged)
    # ----------------------------------------------------
    def setup(self):
        self._ltimer = Label(self, bg="black", fg="#00ff00",
                             font=("Courier New", 18),
                             text="Time left: ")
        self._ltimer.grid(row=1, column=0, columnspan=3, sticky=W)

        self._lkeypad = Label(self, bg="black", fg="#00ff00",
                              font=("Courier New", 18),
                              text="Keypad phase: ")
        self._lkeypad.grid(row=2, column=0, columnspan=3, sticky=W)

        self._lwires = Label(self, bg="black", fg="#00ff00",
                             font=("Courier New", 18),
                             text="Wires phase: ")
        self._lwires.grid(row=3, column=0, columnspan=3, sticky=W)

        self._lbutton = Label(self, bg="black", fg="#00ff00",
                              font=("Courier New", 18),
                              text="Button phase: ")
        self._lbutton.grid(row=4, column=0, columnspan=3, sticky=W)

        self._ltoggles = Label(self, bg="black", fg="#00ff00",
                               font=("Courier New", 18),
                               text="Toggles phase: ")
        self._ltoggles.grid(row=5, column=0, columnspan=2, sticky=W)

        self._lstrikes = Label(self, bg="black", fg="#00ff00",
                               font=("Courier New", 18),
                               text="Strikes left: ")
        self._lstrikes.grid(row=5, column=2, sticky=W)

        if (SHOW_BUTTONS):
            self._bpause = tkinter.Button(self, bg="red", fg="white",
                                          font=("Courier New", 18),
                                          text="Pause",
                                          anchor=CENTER,
                                          command=self.pause)
            self._bpause.grid(row=6, column=0, pady=40)

            self._bquit = tkinter.Button(self, bg="red", fg="white",
                                         font=("Courier New", 18),
                                         text="Quit",
                                         anchor=CENTER,
                                         command=self.quit)
            self._bquit.grid(row=6, column=2, pady=40)


    # lets us pause/unpause the timer (7-segment display)
    def setTimer(self, timer):
        self._timer = timer

    # lets us turn off the pushbutton's RGB LED
    def setButton(self, button):
        self._button = button

    # pauses the timer
    def pause(self):
        if (RPi):
            self._timer.pause()

    # setup the conclusion GUI (explosion/defusion)
    def conclusion(self, success=False):
        # destroy/clear widgets that are no longer needed
        self._lscroll["text"] = ""
        self._ltimer.destroy()
        self._lkeypad.destroy()
        self._lwires.destroy()
        self._lbutton.destroy()
        self._ltoggles.destroy()
        self._lstrikes.destroy()
        if (SHOW_BUTTONS):
            self._bpause.destroy()
            self._bquit.destroy()

        # reconfigure the GUI
        # the retry button
        self._bretry = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Retry", anchor=CENTER, command=self.retry)
        self._bretry.grid(row=1, column=0, pady=40)
        # the quit button
        self._bquit = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Quit", anchor=CENTER, command=self.quit)
        self._bquit.grid(row=1, column=2, pady=40)

    # re-attempts the bomb (after an explosion or a successful defusion)
    def retry(self):
        # re-launch the program (and exit this one)
        os.execv(sys.executable, ["python3"] + [sys.argv[0]])
        exit(0)

    # quits the GUI, resetting some components
    def quit(self):
        if (RPi):
            # turn off the 7-segment display
            self._timer._running = False
            self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            # turn off the pushbutton's LED
            for pin in self._button._rgb:
                pin.value = True
        # exit the application
        exit(0)

# template (superclass) for various bomb components/phases
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(name=name, daemon=True)
        # phases have an electronic component (which usually represents the GPIO pins)
        self._component = component
        # phases have a target value (e.g., a specific combination on the keypad, the proper jumper wires to "cut", etc)
        self._target = target
        # phases can be successfully defused
        self._defused = False
        # phases can be failed (which result in a strike)
        self._failed = False
        # phases have a value (e.g., a pushbutton can be True/Pressed or False/Released, several jumper wires can be "cut"/False, etc)
        self._value = None
        # phase threads are either running or not
        self._running = False

# the timer phase
class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        # the default value is the specified initial value
        self._value = initial_value
        # is the timer paused?
        self._paused = False
        # initialize the timer's minutes/seconds representation
        self._min = ""
        self._sec = ""
        # by default, each tick is 1 second
        self._interval = 1

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            if (not self._paused):
                # update the timer and display its value on the 7-segment display
                self._update()
                self._component.print(str(self))
                # wait 1s (default) and continue
                sleep(self._interval)
                # the timer has expired -> phase failed (explode)
                if (self._value == 0):
                    self._running = False
                self._value -= 1
            else:
                sleep(0.1)

    # updates the timer (only internally called)
    def _update(self):
        self._min = f"{self._value // 60}".zfill(2)
        self._sec = f"{self._value % 60}".zfill(2)

    # pauses and unpauses the timer
    def pause(self):
        # toggle the paused state
        self._paused = not self._paused
        # blink the 7-segment display when paused
        self._component.blink_rate = (2 if self._paused else 0)

    # returns the timer as a string (mm:ss)
    def __str__(self):
        return f"{self._min}:{self._sec}"

# the keypad phase
class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad"):
        super().__init__(name, component, target)
        # the default value is an empty string
        self._value = ""

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            # process keys when keypad key(s) are pressed
            if (self._component.pressed_keys):
                # debounce
                while (self._component.pressed_keys):
                    try:
                        # just grab the first key pressed if more than one were pressed
                        key = self._component.pressed_keys[0]
                    except:
                        key = ""
                    sleep(0.1)
                # log the key
                self._value += str(key)
                # the combination is correct -> phase defused
                if (self._value == self._target):
                    self._defused = True
                # the combination is incorrect -> phase failed (strike)
                elif (self._value != self._target[0:len(self._value)]):
                    self._failed = True
            sleep(0.1)

    # returns the keypad combination as a string
    def __str__(self):
        if (self._defused):
            return "DEFUSED"
        else:
            return self._value

# the jumper wires phase
class Wires(PhaseThread):
    def __init__(self, component, target, name="Wires"):
        super().__init__(name, component, target)

    # runs the thread
    def run(self):
        # TODO
        pass

    # returns the jumper wires state as a string
    def __str__(self):
        if (self._defused):
            return "DEFUSED"
        else:
            # TODO
            pass

# the pushbutton phase
class Button(PhaseThread):
    def __init__(self, component_state, component_rgb, target, color, timer, name="Button"):
        super().__init__(name, component_state, target)
        # the default value is False/Released
        self._value = False
        # has the pushbutton been pressed?
        self._pressed = False
        # we need the pushbutton's RGB pins to set its color
        self._rgb = component_rgb
        # the pushbutton's randomly selected LED color
        self._color = color
        # we need to know about the timer (7-segment display) to be able to determine correct pushbutton releases in some cases
        self._timer = timer

    # runs the thread
    def run(self):
        self._running = True
        # set the RGB LED color
        self._rgb[0].value = False if self._color == "R" else True
        self._rgb[1].value = False if self._color == "G" else True
        self._rgb[2].value = False if self._color == "B" else True
        while (self._running):
            # get the pushbutton's state
            self._value = self._component.value
            # it is pressed
            if (self._value):
                # note it
                self._pressed = True
            # it is released
            else:
                # was it previously pressed?
                if (self._pressed):
                    # check the release parameters
                    # for R, nothing else is needed
                    # for G or B, a specific digit must be in the timer (sec) when released
                    if (not self._target or self._target in self._timer._sec):
                        self._defused = True
                    else:
                        self._failed = True
                    # note that the pushbutton was released
                    self._pressed = False
            sleep(0.1)

    # returns the pushbutton's state as a string
    def __str__(self):
        if (self._defused):
            return "DEFUSED"
        else:
            return str("Pressed" if self._value else "Released")

# the toggle switches phase
class Toggles(PhaseThread):
    def __init__(self, component, target, name="Toggles"):
        super().__init__(name, component, target)

    # runs the thread
    def run(self):
        # TODO
        pass

    # returns the toggle switches state as a string
    def __str__(self):
        if (self._defused):
            return "DEFUSED"
        else:
            # TODO
            pass
