from contextlib import suppress
from os import _exit
from random import randint, random, uniform
from threading import Thread
from time import sleep, gmtime, strftime, time
from tkinter import *
from tkinter.filedialog import askopenfilename


class Trainer:
    def __init__(self):
        self.window = Tk()
        self.window.geometry('1280x720')
        self.window.title("Mouse Accuracy Test")
        self.window.config(bg='#1E272E')
        self.window.protocol("WM_DELETE_WINDOW", self.exit_program)

        self.registered_buttons = []
        self.total_lives = 5
        self.session_lives = self.total_lives
        self.elapsed_time = 0
        self.highest_time = 0
        self.active_match = True
        self.recent_file = None
        self.time_started = time()

        self.menu_frame = self._menu()
        self.start_button = Button(self.window, text='P L A Y', fg='#1E272E', bg='WHITE', font='Bahnschrift 26 bold', bd=0, width=20, command=lambda: (self.menu_frame.place(x=0, y=0), self.start_button.place_forget()))
        self.start_button.place(relx=.340625, rely=.425)
        self.lives_counter = Label(self.window, text='', fg='white', bg='#1E272E', font='Bahnschrift 16 bold', width=5)
        self.lives_counter.place(relx=.93, rely=.925)

        self.window.mainloop()

    def _menu(self):
        menu_frame = Frame(self.window, bg='#1E272E', width=1280, height=720)
        quick_play = Button(menu_frame, text='R A N D O M', fg='#1E272E', bg='WHITE', font='Bahnschrift 26 bold', bd=0, width=20, command=lambda: (self.match_random(), menu_frame.place_forget()))
        quick_play.place(relx=.340625, rely=.4)
        load_file = Button(menu_frame, text='L O A D  F R O M  F I L E', fg='#1E272E', bg='WHITE', font='Bahnschrift 22 bold', bd=0, width=25, command=lambda: (menu_frame.place_forget(), self.ask_file()))
        load_file.place(relx=.340625, rely=.5)
        return menu_frame

    def _match_random(self):
        while self.active_match:
            if self.total_lives <= 0:
                self.finish_match(); break
            self.spawn_box()
            sleep(random() * randint(1, 3))

    def match_random(self):
        self.time_started = time()
        self.recent_file = None
        self.session_lives = self.total_lives
        Thread(target=self._match_random).start()

    def notification(self, text, colour, delay=7):
        alert = Label(self.window, text="!", bg=colour, fg='#1E272E', font='Bahnschrift 14 bold', width=2)
        alert.place(relx=.03, rely=.05)
        message = Label(self.window, text=text, justify=LEFT, bg='#1E272E', fg=colour, font=('Consolas', 14, 'bold'))
        message.place(relx=.0625, rely=.05)
        self.window.after(delay * 1000, lambda: (alert.place_forget(), message.place_forget()))

    def reset(self):
        self.total_lives = 5
        self.registered_buttons = []
        self.elapsed_time = 0
        self.active_match = True
        self.stopwatch_active = True
        self.window.config(bg='#1E272E')
        self.lives_counter.config(text='')

    def ask_file(self):
        file_path = askopenfilename(filetypes=(("text files", "*.txt"), ("all files", "*.*")))
        if not file_path:
            self.notification("Please select a valid file.", colour="#e74c3c")
            self.menu_frame.place(x=0, y=0)
            return
        parsed_file = self.parse_file(open(file_path, 'r'))
        if parsed_file:
            self.recent_file = open(file_path, 'r')
            self.match_file(self.recent_file)
        else:
            self.menu_frame.place(relx=0, rely=0)
            
    def parse_file(self, file):
        VALID_ACTIONS = ['BOX', 'WAIT', 'FOREGROUND', 'RANDOM', 'BACKGROUND', 'LIVES']
        file_lines = file.readlines()
        line_count = 0
        self.total_lives = 5
        self.session_lives = self.total_lives
        for line in file_lines:
            if not self.active_match:
                break
            line_count += 1
            action = line.strip().replace(' ', '').split(':')
            if action[0] not in VALID_ACTIONS and not (action[0] == '' or action[0].startswith('#')):
                self.notification(f"File parsing error on line {line_count}.", colour="#e74c3c"); return
            if action[0] in ['BOX', 'WAIT', 'FOREGROUND', 'BACKGROUND', 'LIVES']:
                if len(action) == 1:
                    self.notification(f"File parsing error on line {line_count}, missing argument.", colour="#e74c3c"); return
            if action[0] == 'WAIT':
                if not action[1].replace('.', '', 1).isdigit():
                    self.notification(f"File parsing error on line {line_count}, invalid argument (format).", colour="#e74c3c"); return
            elif action[0] == 'BOX':
                coordinates = action[1].replace(' ', '').split(',')
                for coordinate in coordinates:
                    if not coordinate.replace('.', '', 1).isdigit() or len(coordinates) != 4:
                        self.notification(f"File parsing error on line {line_count}, invalid argument.", colour="#e74c3c"); return
                if not (0.9 >= float(coordinates[1]) >= 0 or 0.9 >= float(coordinates[2]) >= 0):
                    self.notification(f"File parsing error on line {line_count}, invalid argument (out of bounds).", colour="#e74c3c"); return
            elif action[0] == 'LIVES':
                if not action[1].strip().isdigit():
                    self.notification(f"File parsing error on line {line_count}, invalid argument (format).", colour="#e74c3c"); return
                self.total_lives = int(action[1])
                self.session_lives = self.total_lives
            elif action[0] in ['FOREGROUND', 'BACKGROUND']:
                colour = action[1]
                if len(colour) == 0:
                    self.notification(f"File parsing error on line {line_count}, invalid argument (requires hex colour).", colour="#e74c3c"); return
        return True

    def _late_destroy(self, identifier, delay):
        button_copy = identifier
        colour = bytes.fromhex(button_copy.cget("bg").replace('#', ''))
        colour_bg = bytes.fromhex(self.window.cget("bg").replace('#', ''))
        difference = tuple(map(lambda i, j: i - j, colour, colour_bg))
        difference_interval = tuple(di // 50 for di in difference)
        for _ in range(50):
            if identifier not in self.registered_buttons:
                break
            with suppress(TclError):
                colour = tuple(map(lambda i, j: i - j, colour, difference_interval))
                button_copy.config(bg='#%02x%02x%02x' % colour)
            sleep(float(delay) / 50)
        if identifier in self.registered_buttons:
            button_copy.place_forget()
            self.total_lives -= 1
            self.lives_counter.config(text=self.total_lives)
            self.registered_buttons.remove(identifier)

    def _match_file(self, file):
        foreground_colour = '#FFFFFF'
        background_colour = '#1E272E'
        while True:
            file.seek(0)
            for line in file.readlines():
                if self.total_lives <= 0:
                    self.finish_match(); return
                action = line.strip().replace(' ', '').split(':')
                if action[0] == 'BOX':
                    arguments = action[1].replace(' ', '').split(',')
                    self.spawn_box(size=int(arguments[0]), x=float(arguments[1]), y=float(arguments[2]), colour=foreground_colour, delay=float(arguments[3]))
                elif action[0] == 'WAIT':
                    arguments = action[1].replace(' ', '').split(',')
                    sleep(float(arguments[0]))
                elif action[0] == 'RANDOM':
                    self.spawn_box(colour=foreground_colour)
                    sleep(random() * randint(2, 4))
                elif action[0] in ['FOREGROUND', 'BACKGROUND']:
                    with suppress(TclError):
                        self.window.config(bg=action[1])
                        if action[0] == 'FOREGROUND':
                            self.window.config(bg=background_colour)
                            foreground_colour = action[1]
                        else:
                            background_colour = action[1]

    def match_file(self, file):
        self.time_started = time()
        self.total_lives = self.session_lives
        self.lives_counter.config(text=self.total_lives)
        Thread(target=self._match_file, args=(file, )).start()

    def spawn_box(self, **kwargs):
        coordinates = [kwargs.get('x', uniform(0, 0.9)), kwargs.get('y', uniform(0, 0.9))]
        colour = kwargs.get('colour', '#FFFFFF')
        size = kwargs.get('size', randint(1, 3))
        box_button = Button(self.window, bd=0, width=size * 2, height=size, bg=colour, font='Bahnschrift 16 bold')
        box_button.configure(command=lambda b=box_button: self.register_click(b))
        box_button.place(relx=coordinates[0], rely=coordinates[1])
        self.registered_buttons.append(box_button)
        Thread(target=self._late_destroy, args=(box_button, kwargs.get('delay', random() * randint(2, 5)))).start()

    def register_click(self, button):
        self.registered_buttons.remove(button)
        button.place_forget()

    def finish_match(self):
        final_frame = Frame(bg="#30336b", width=1280, height=720)
        self.elapsed_time = time() - self.time_started
        if self.elapsed_time > self.highest_time:
            self.highest_time = self.elapsed_time
            Label(final_frame, bg='#30336b', fg='#bdc3c7', text='You got a new high score!', font='Bahnschrift 12 bold').place(relx=.5215, rely=.535)
        if self.recent_file:
            Button(final_frame, text=' R E P L A Y   L E V E L ', fg='#30336b', bg='WHITE', font='Bahnschrift 12 bold', bd=0, width=21, command=lambda: (final_frame.place_forget(), self.reset(), self.match_file(self.recent_file))).place(relx=.35, rely=.535)
        Label(final_frame, fg='#30336b', bg='#FFFFFF', text='G A M E   O V E R', font='Bahnschrift 22 bold', width=20).place(relx=.35, rely=.35)
        Label(final_frame, fg='#30336b', bg='#FFFFFF', text='E l a p s e d   T i m e', font='Bahnschrift 18 bold', width=21).place(relx=.35, rely=.425)
        Label(final_frame, bg='#30336b', fg='#FFFFFF', text=' '.join(list(strftime("%M:%S." + str(int((self.elapsed_time % 1) * 10)), gmtime(self.elapsed_time)))), font='Bahnschrift 18 bold').place(relx=.58, rely=.425)
        Label(final_frame, fg='#30336b', bg='#FFFFFF', text='L o n g e s t   T i m e', font='Bahnschrift 18 bold', width=21).place(relx=.35, rely=.48)
        Label(final_frame, bg='#30336b', fg='#FFFFFF', text=' '.join(list(strftime("%M:%S." + str(int((self.highest_time % 1) * 10)), gmtime(self.highest_time)))), font='Bahnschrift 18 bold').place(relx=.58, rely=.48)
        Button(final_frame, text='▶', fg='#30336b', bg='#FFFFFF', font='Bahnschrift 16', bd=0, width=5, command=lambda: (final_frame.place_forget(), self.reset(), self.start_button.place(relx=.340625, rely=.425))).place(relx=.6175, rely=.3505)
        final_frame.place(x=0, y=0)

    def exit_program(self):
        self.window.destroy()
        _exit(1)


if __name__ == '__main__':
    Trainer()
