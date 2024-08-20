# ______READ ME______
# 
# SUBMISSION TRANSFER APP
# 
# Authors:
# Christopher Elwell
# Steven Louie
# Ayla Cillers
# UBC APSC CIS 2024
# 
# MAIN FUNCTION: uses Canvas api to transfer an assignment and the assignment's student submissions
# from a source course to a destination course, entered via the user interface as links to the assignment
# and destination course
#
# OPTIONS: Users can select the name of the copied assignment and can select which student to transfer the submissions for
#
# SECURITY: Requires users to select a .txt file with their Canvas Token to gain access to the app. Does not request users actually
# enter their key into the application.
#
# DOCUMENTATION: Includes short tutorials on how to use the app
# 
# NOTES: Uses customtkinter to create the UI and canvasapi to access canvas. Packaged into a .exe with pyinstaller and auto-py-to-exe.
# Almost everything to do with the actual assignment and submission transfer occurs in the run_script and 
# copy_assignment functions within the main_app class. 

import os
from canvasapi import Canvas, exceptions as c_exceptions
from pathlib import Path
from customtkinter import*
from PIL import Image
import tkinter as tk
import re
import webbrowser

DEFAULT_TOKEN = 'mytoken.txt'  # Text file with your api token saved in the same directory as this script
CANVAS_URL = "https://canvas.ubc.ca"
DOCUMENTATION_LINK = "https://canvas.instructure.com/doc/api/courses.html"

UBC_BLUE = "#002145"
LIGHT_BLUE = "#6EC4E8"
HOVER = "#0680A6"

class main_app(CTk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        
        global SMALL_FONT
        SMALL_FONT = CTkFont('Lato',16)

        global BIG_FONT
        BIG_FONT = CTkFont('Lato',30)

        set_appearance_mode('light')

        self.get_token_window = None
        self.define_sizes()
        self.geometry(f"{self.window_width}x{self.window_height}")
        self.title('Submission Transfer App')

        self.source_course_id = None
        self.source_assignment_id = None
        self.destination_course_id = None

        self.docs = None

        self.resizable(False,False)
        self.UI_setup()
        self.bindings()

        self.canvas = None
        self.get_token()
    
    def define_sizes(self):
        self.inner_corner_radius = 0
        self.window_width = 1000
        self.header_height = 80
        self.title_height = 50
        self.mainframe_height = 675
        self.spacer_width = 20
        self.small_spacer_width = 10
        self.btns_height = 60
        self.box_width = (self.window_width - 3 * self.spacer_width) / 2
        self.btn_width = (self.box_width - self.spacer_width) / 2
        self.inner_box_width = (self.box_width - 2*self.spacer_width)
        self.inputs_height = self.mainframe_height - 2 * self.spacer_width
        self.outputs_height = self.mainframe_height - 3 * self.spacer_width - self.btns_height
        self.window_height = self.header_height+self.title_height+self.mainframe_height
        self.student_frame_height = self.inputs_height - 40 * 4 - self.spacer_width * 4 - 55
        self.column1_width = 0.9 * self.inner_box_width - self.spacer_width
        self.column2_width = 0.1 * self.inner_box_width

    def UI_setup(self):
        self.header = CTkFrame(self,self.window_width,self.header_height,fg_color="white",bg_color="white")
        self.logo_image = CTkImage(light_image=Image.open(self.resource_path("ubc_header.png")),size=(round(768*0.588235),60))
        self.logo_label = CTkLabel(self.header, image=self.logo_image, text="",fg_color="white",bg_color="white")
        self.logo_label.pack(pady=10,anchor="w",padx=30)
        self.header.grid(sticky = "news",column = 0, row = 0)
        self.rowconfigure([0,3],minsize=self.header_height)

        self.title_frame = CTkFrame(self,self.window_width,self.title_height,fg_color=UBC_BLUE,bg_color=UBC_BLUE)
        self.title_label = CTkLabel(self.title_frame,self.window_width,text="Submission Transfer App", 
                                    font = BIG_FONT,text_color="white",anchor="w",
                                    fg_color=UBC_BLUE,bg_color=UBC_BLUE)
        self.title_label.place(rely = 0.5, relx = 0.52, anchor = CENTER)

        self.user_name = CTkLabel(self.title_frame,text = "", text_color="white",font = SMALL_FONT,anchor = "e")
        self.user_name.place(rely = 0.5, x = self.window_width - self.spacer_width, relheight = 1, relwidth = 0.5,anchor = "e")
        
        self.title_frame.grid(column = 0, row = 1, sticky = "news")
        
        self.mainframe = CTkFrame(self,self.window_width,self.mainframe_height,fg_color="white", bg_color="white")
        self.mainframe.grid(column = 0, row = 2, sticky = "news")

        self.inputs_box = CTkFrame(self.mainframe,fg_color=UBC_BLUE,corner_radius=0,width = self.box_width)
        self.inputs_box.place(relx = (self.spacer_width + self.box_width/2)/self.window_width,rely=0.5, relheight = self.inputs_height/self.mainframe_height, anchor=CENTER)

        self.outputs_box = CTkFrame(self.mainframe,fg_color=UBC_BLUE,corner_radius=0,width = self.box_width)
        self.outputs_box.place(x=self.window_width-self.spacer_width-self.box_width/2,y=self.spacer_width + self.outputs_height / 2,relheight = self.outputs_height/self.mainframe_height,anchor=CENTER)

        self.inputs = CTkFrame(self.inputs_box,corner_radius=10,bg_color=UBC_BLUE,fg_color=UBC_BLUE,width = self.inner_box_width)
        self.inputs.place(relx=0.5,rely=0.5,relheight = (self.inputs_height - 2*self.spacer_width)/self.inputs_height,anchor=CENTER)

        self.outputs = CTkFrame(self.outputs_box,fg_color=UBC_BLUE,corner_radius=10,bg_color=UBC_BLUE,width = self.inner_box_width)
        self.outputs.place(relx=0.5,rely=0.5,relheight = (self.outputs_height - 2*self.spacer_width)/self.outputs_height,anchor=CENTER)

        self.inputs.columnconfigure(0,minsize=self.column1_width,pad = 20)
        self.inputs.columnconfigure(1,minsize=self.column2_width)
        self.inputs.rowconfigure([1,2,3,4], pad=20)

        self.source_assignment_label = CTkLabel(self.inputs,width = self.column1_width, height = 40, text="Source Assignment", font=BIG_FONT,anchor='w',text_color="white")
        self.source_assignment_label.grid(column = 0, row = 0,sticky = "w")

        self.source_assignment_entry = CTkEntry(self.inputs,width = self.column1_width,height=40,corner_radius = self.inner_corner_radius,
                                           text_color=UBC_BLUE,fg_color='white',
                                           placeholder_text_color=UBC_BLUE,
                                           placeholder_text="Insert Assignment Link",
                                           font = SMALL_FONT,border_width=0)
        self.source_assignment_entry.grid(column = 0, row = 1,sticky = "w")
        
        self.source_assignment_entry_question = CTkButton(self.inputs,width = self.column2_width,height=40,corner_radius = self.inner_corner_radius,
                                                     text="?",font = ('Lato',30),fg_color=HOVER, text_color='white',command = lambda: self.open_docs(2))
        self.source_assignment_entry_question.grid(column = 1, row = 1, sticky = "w")

        self.source_assignment_display = CTkLabel(self.inputs, width = self.inner_box_width, height = 60, text="",
                                              font = ("Lato",16),corner_radius = self.inner_corner_radius,fg_color='white',text_color=UBC_BLUE,justify = "left",anchor = "w")
        self.source_assignment_display.grid(column = 0, row = 2, columnspan = 2,sticky = 'w')

        self.source_assignment_label = CTkLabel(self.inputs,width = self.column1_width, height = 40, text="Choose Students", font=BIG_FONT,anchor='w',text_color="white")
        self.source_assignment_label.grid(column = 0, row = 3,sticky = "w")

        self.choose_students = Student_Choice_Frame(self.inputs,self,self.inner_box_width,self.student_frame_height)
        self.choose_students.grid(column = 0, row = 4, columnspan = 2, sticky = "w")

        self.outputs.columnconfigure(0, minsize=self.column1_width,pad = 20)
        self.outputs.columnconfigure(1, minsize=self.column2_width)
        self.outputs.rowconfigure([1,2,4,5,7], pad=20)
        self.outputs.rowconfigure(3,minsize=0)
        self.outputs.rowconfigure(6,minsize=0)

        self.destination_course_label = CTkLabel(self.outputs,width = self.column1_width,height = 40,
                                            text = "Destination Course",font = ('Lato', 30), 
                                            anchor='w',text_color="white")
        self.destination_course_label.grid(column = 0, row = 0, sticky = "sw")
        
        self.dest_course_entry_question = CTkButton(self.outputs,width = self.column2_width,height=40,corner_radius = self.inner_corner_radius,
                                                     text="?",font = ('Lato',30),fg_color=HOVER, text_color='white',command = lambda: self.open_docs(1))
        self.dest_course_entry_question.grid(column = 1, row = 1, sticky = "w")

        self.destination_course_entry = CTkEntry(self.outputs,width = self.column1_width,height=40,corner_radius = self.inner_corner_radius,
                                           text_color=UBC_BLUE,fg_color='white',bg_color='white',
                                           placeholder_text_color=UBC_BLUE,
                                           placeholder_text="Insert Course Link",
                                           font = SMALL_FONT,border_width=0)
        self.destination_course_entry.grid(column = 0, row = 1,sticky = "w")
        

        self.destination_course_display = CTkLabel(self.outputs, width = self.inner_box_width, height = 60, text="",
                                              font = ("Lato",16),corner_radius = self.inner_corner_radius,fg_color='white',text_color=UBC_BLUE,anchor="w")
        self.destination_course_display.grid(column = 0, row = 2, columnspan = 2,sticky = 'w')

        self.assignment_name_label = CTkLabel(self.outputs,width = self.column1_width, height = 40, text="New Assignment Name", font = ('Lato',30),anchor='w',text_color="white")
        self.assignment_name_label.grid(column = 0, row = 4,sticky = 'w')

        self.name_choice_frame = CTkFrame(self.outputs, bg_color=UBC_BLUE,fg_color=UBC_BLUE,width=self.column1_width,height = 100)
        self.name_choice_var = tk.IntVar(value = 1)
        self.name_choice_same = CTkRadioButton(self.name_choice_frame, text = "Same",variable = self.name_choice_var, 
                                                value = 1, font = SMALL_FONT,command=self.on_name_choice_select,
                                                text_color='white',fg_color=HOVER,hover_color=HOVER,border_width_checked=5,
                                                border_width_unchecked=3)
        self.name_choice_new = CTkRadioButton(self.name_choice_frame, text = "New",variable = self.name_choice_var, 
                                                value = 2, font = SMALL_FONT,command=self.on_name_choice_select,
                                                text_color='white',fg_color=HOVER,hover_color=HOVER,border_width_checked=5,
                                                border_width_unchecked=3)
        self.name_choice_same.place(relx = 0,rely = 0.5,relheight=0.5,relwidth=0.25,anchor="nw")
        self.name_choice_new.place(relx = 0,rely = 0,relheight=0.5,relwidth=0.25,anchor="nw")
        self.name_choice_frame.grid(column = 0, row = 5,sticky = "w")

        self.assignment_name_var = tk.StringVar()
        self.assignment_name_holder = "Insert Assignment Name"
        self.assignment_name_var.set("Same as Source Assignment")
        self.assignment_name_entry = CTkEntry(self.outputs,width = self.inner_box_width,
                                              height=40,corner_radius=self.inner_corner_radius,
                                           text_color="grey",fg_color='white',font =SMALL_FONT,
                                           textvariable=self.assignment_name_var,border_width=0)
        self.assignment_name_entry.grid(column = 0, row = 7,columnspan = 2,sticky = "w")

        self.run_btn_frame = CTkFrame(self.mainframe,bg_color='White',fg_color='White',width = self.box_width, height = self.btns_height)
        self.run_btn_frame.place(x = self.window_width - self.spacer_width - self.box_width/2, y = self.mainframe_height - self.spacer_width - self.btns_height / 2, anchor = CENTER)
        self.run_btn = CTkButton(self.run_btn_frame,text="Run",
                                 fg_color=UBC_BLUE,bg_color = 'white',corner_radius=0,
                                 font = ('Lato',30),text_color="white",hover_color=HOVER,
                                 command = self.run_script, state = "disabled")
        self.run_btn.place(x = self.btn_width * 3/2 + self.spacer_width, rely = 0.5, relwidth = 1/2 - self.spacer_width/(2 * self.box_width), relheight = 1, anchor = CENTER)
        self.disclaimer_btn = CTkButton(self.run_btn_frame,text="Documentation",
                                 fg_color=UBC_BLUE,bg_color = 'white',corner_radius=0,
                                 font = ('Lato',20),text_color="white",hover_color=HOVER,
                                 width = 200, height = 60,command = lambda: self.open_docs(1))
        self.disclaimer_btn.place(x = self.btn_width / 2, rely = 0.5, relwidth = (225)/470, relheight = 1, anchor = CENTER)

    def resource_path(self,relative_path):
        try:
            # PyInstaller creates a temporary folder and stores the path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def open_docs(self,index):
        if self.docs is None:
            self.docs = Documentation(self,index)
        else:
            self.docs.focus()
        if index == 0:
            self.docs.grab_set()

    def bindings(self):
        self.bind_all('<Button-1>', self.handle_focus)
        self.source_assignment_entry.bind('<Button-1>',lambda event: self.source_assignment_entry.delete(0,tk.END))
        self.destination_course_entry.bind('<Button-1>',lambda event: self.destination_course_entry.delete(0,tk.END))
        self.destination_course_entry.bind('<Return>',self.read_destination_course_entry)
        self.source_assignment_entry.bind('<Return>',self.read_assignment_entry)

    def on_name_choice_select(self):
        value = self.name_choice_var.get()
        if value == 1:
            self.assignment_name_entry.configure(state = "disabled",text_color = "grey")
            self.assignment_name_var.set("Same as Source Assignment")
            self.assignment_name_entry.unbind('<Return>')
        else:
            self.assignment_name_entry.configure(state = "normal",text_color=UBC_BLUE)
            self.assignment_name_var.set(self.assignment_name_holder)
            self.assignment_name_entry.bind('<Return>',self.on_enter_assignment_name)
    
    def on_enter_assignment_name(self,event):
        self.assignment_name_holder = self.assignment_name_var.get()
        self.focus_set()

    def read_assignment_entry(self,event):
        self.focus_set()
        link = event.widget.get()
        code = self.get_course_code(link, 'assignment')
        if code[0]:
            try:
                course = self.canvas.get_course(code[1])
                assignment = course.get_assignment(code[2])
            except c_exceptions.ResourceDoesNotExist:
                text = "   No course/assignment found"
                self.source_course_id = None
                self.source_assignment_id = None
                self.enable_run_check()
            except (c_exceptions.Unauthorized):
                text = "   You don't have the priveledges to access this course"
                self.source_course_id = None
                self.source_assignment_id = None
                self.enable_run_check()
            else:
                text = "   Course: " + course.name + \
                     "\n   Assignment: " + assignment.name
                self.source_course_id = code[1]
                self.source_assignment_id = code[2]
                self.enable_run_check()
        else:
            text = "   This doesn't look like an assignment link to me"
            self.source_course_id = None
            self.source_assignment_id = None
            self.enable_run_check()
        self.source_assignment_display.configure(text = text)
        
    def read_destination_course_entry(self,event):
        self.focus_set()
        link = event.widget.get()
        code = self.get_course_code(link,'course')
        if (code[0]):
            try:
                course = self.canvas.get_course(code[1])
                course_name = "   Course: " + course.name
            except c_exceptions.ResourceDoesNotExist:
                course_name = "   No course found"
                self.destination_course_id = None
                self.enable_run_check()
            else:
                self.destination_course_id = code[1]
                self.enable_run_check()
        else:
            course_name = "   This doesn't look like a course link to me"
            self.destination_course_id = None
            self.enable_run_check()
        self.destination_course_display.configure(text = course_name) 
    
    def handle_focus(self,event):
        if isinstance(event.widget,tk.Entry):
            event.widget.focus_set()
        else:
            self.focus_set()

    def enable_run_check(self):
        if self.source_assignment_id and self.source_course_id and self.destination_course_id:
            self.run_btn.configure(state = "normal")
            self.choose_students.enable_all()
            self.choose_students.update_table()
            print("normal")
        else: 
            self.run_btn.configure(state = "disabled")
            self.choose_students.disable_all()
            print("disabled")

    def get_course_code(self,link,type):
        course_pattern = r"(?<=courses/)(\d+)"
        course_code = re.findall(course_pattern,link)
        if type == "course" and course_code:
            return (True,int(course_code[0]))
        elif type == "assignment" and course_code:
            assignment_pattern = r"(?<=assignments/)(\d+)"
            assignment_code = re.findall(assignment_pattern,link)
            if assignment_code:
                return (True,int(course_code[0]),int(assignment_code[0]))
        return (False, None)
            
    def get_token(self):
        result, canvas = self.load_token()
        if result:
            self.canvas = canvas
            self.user_name.configure(text = canvas.get_current_user().name)
        else:
            self.open_token_finder(result)

    def open_token_finder(self,result):
        if self.get_token_window is None or not self.get_token_window.winfo_exists():
            self.get_token_window = Get_Token(result,self)  # create window if its None or destroyed
            self.get_token_window.grab_set()

        else:
            self.get_token_window.focus()  # if window exists focus it
    
    def load_token(self,token_path=DEFAULT_TOKEN):
        if Path(token_path).exists() and Path(token_path).is_file():
            with open(token_path, 'r') as token_file:
                api_key = token_file.read()
                canvas = Canvas(CANVAS_URL, api_key)
                try:
                    if canvas.get_current_user():  # check to see if api key is valid by getting the user associated to it
                        return 2, canvas
                except (c_exceptions.InvalidAccessToken, c_exceptions.ResourceDoesNotExist):
                    return 1, None
        return 0, None
    
    def copy_assignment(self,assignment_to_copy, destination_course,assignment_name):
        assignment_params = {
            "name": assignment_name,
            "description": assignment_to_copy.description,
            "points_possible": assignment_to_copy.points_possible,
            "submission_types": ['online_upload'],  
            "due_at": assignment_to_copy.due_at,
            "unlock_at": assignment_to_copy.unlock_at,
            "lock_at": assignment_to_copy.lock_at,
            "published": True,
            "allowed_extensions":assignment_to_copy.allowed_extensions
        }

        new_assignment = destination_course.create_assignment(assignment_params)
        if new_assignment:
            return new_assignment
        else:
            self.warning("Assignment not made")
            return

    def warning(self,text):
        warning_window = Warning_Window(text,self)
        warning_window.grab_set()

    def run_script(self):        
        loading_screen = Loading_Done_Window(self)
        loading_screen.grab_set()
        source_course = self.canvas.get_course(self.source_course_id)
        source_assignment = source_course.get_assignment(self.source_assignment_id, include = ["submission"])
        destination_course = self.canvas.get_course(self.destination_course_id)

        if self.run_checks(source_course,source_assignment,destination_course):
            return

        if (self.name_choice_var.get() == 1):
            assignment_name = source_assignment.name
        else: 
            assignment_name = self.assignment_name_var.get()
            if len(assignment_name) == 0:
                self.warning("Assignment name cannot be blank.")
                return

        assignments_in_destination_course = destination_course.get_assignments()

        assignment_name = self.get_assignment_name(assignment_name,0,assignments_in_destination_course)

        submissions = source_assignment.get_submissions()
        new_assignment = self.copy_assignment(source_assignment,destination_course,assignment_name)

        students_chosen = self.choose_students.get_chosen_students()

        if new_assignment:
            for s in submissions:
                if (s.user_id in students_chosen):
                    attachments = s.attachments
                    for a in attachments:
                        submission_file_id = a.id

                        submission = {  # ←↓ Your code had an incorrect indentation for this part.
                            "user_id": s.user_id,
                            "submission_type": 'online_upload',  # ← Changed to "online_upload" instead of "online_url"
                            'file_ids': [submission_file_id]
                        }
                        new_assignment.submit(submission)
        loading_screen.finished(f"{CANVAS_URL}/courses/{self.destination_course_id}/assignments/{new_assignment.id}")

    def run_checks(self,source,assignment,destination):
        if source.id == destination.id:
            self.warning("Source and destination courses are the same course")
            return True
        elif assignment.submission_types != ['online_upload']:
            self.warning("Assignment either does not accept or does not exclusively accept online uploads. This is required.")

    def get_assignment_name(self,name,counter,assignments):
        for assignment in assignments:
            if (counter != 0 and name + f" ({counter})" == assignment.name) or (counter == 0 and name == assignment.name):
                return self.get_assignment_name(name,counter+1,assignments)
        if counter == 0:
            return name
        else: 
            return name + f" ({counter})"

class Get_Token(CTkToplevel):
    def __init__(self,result,parent):
        super().__init__(parent)
        self.main = parent
        self.title("Get Access Token")
        self.geometry("400x250")
        self.resizable(False,False)
        self.mainframe = CTkFrame(self,bg_color="white",fg_color="white")
        self.info = CTkLabel(self.mainframe,width=200,height=100,text="",text_color=UBC_BLUE,
                             font = ('Lato',20,'bold'),wraplength = 400*0.75)
        self.info.place(relx = 0.5,rely=0.33,relwidth = 0.75,relheight = 0.3,anchor = CENTER)
        self.update_info(result)
        self.select_file = CTkButton(self.mainframe,corner_radius=0, text = "Get Access Token File",
                                     command=self.browse_files,bg_color=UBC_BLUE,fg_color=UBC_BLUE,
                                     hover_color=HOVER,font = SMALL_FONT, width = 170, height = 40)
        self.select_file.place(x = 20, y = 190, anchor = "nw")
        self.select_file = CTkButton(self.mainframe,corner_radius=0, text = "Help",
                                     command=lambda: self.main.open_docs(0),bg_color=UBC_BLUE,fg_color=UBC_BLUE,
                                     hover_color=HOVER,font = SMALL_FONT, width = 170, height = 40)
        self.select_file.place(x = 210, y = 190, anchor = "nw")
        self.mainframe.place(relx = 0.5, rely = 0.5, relwidth = 1, relheight = 1, anchor = CENTER)

        self.protocol("WM_DELETE_WINDOW",self.on_close)

    def on_close(self):
        self.close_window = Close_Token_Window_Warning(self)
        self.close_window.grab_set()

    def update_info(self,result):
        if result == 1:
            self.info.configure(text = "Access token is invalid.")
        elif result == 0:
            self.info.configure(text = "No token file found. \nPlease select a .txt file with your access token.")
    
    def browse_files(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            result, canvas = self.main.load_token(file_path)
            if result == 2:
                self.main.canvas = canvas
                self.main.user_name.configure(text = canvas.get_current_user().name)
                self.destroy()
            else:
                self.update_info(result)
        else:
            self.update_info(0)

class Close_Token_Window_Warning(CTkToplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.geometry("300x200")
        self.title("Closing Program")

        self.parent = parent

        self.resizable(False,False)

        self.mainframe = CTkFrame(self,fg_color=UBC_BLUE,bg_color=UBC_BLUE)
        self.mainframe.place(relx=0.5,rely=0.5,relheight=1,relwidth=1,anchor = CENTER)
        self.text = CTkLabel(self.mainframe,text = "Selecting an Access Token is mandatory.\n\nThis action will close the program. \nAre you sure?",font = ('Lato',16),text_color="white",wraplength=300*0.8,anchor="center")
        self.text.place(relx = 0.5,rely = 0.3, relwidth = 0.8, relheight = 0.5,anchor = CENTER)
        self.go_back_btn = CTkButton(self.mainframe, text = "Go Back", fg_color="white",
                                     bg_color="white",text_color=UBC_BLUE,hover_color=HOVER,
                                     corner_radius=0,font = SMALL_FONT,command=self.go_back)
        self.go_back_btn.place(relx = 0.3, rely = 0.7,relwidth = 0.3,relheight = 0.2,anchor=CENTER)
        self.close_btn = CTkButton(self.mainframe, text = "Close", fg_color="white",
                                   bg_color="white",text_color=UBC_BLUE,hover_color=HOVER,
                                   corner_radius=0,font = SMALL_FONT,command=self.close)
        self.close_btn.place(relx = 0.7, rely = 0.7,relwidth = 0.3,relheight = 0.2,anchor=CENTER)
        
    def close(self):
        self.parent.main.destroy()

    def go_back(self):
        self.parent.grab_set()
        self.destroy()

class Warning_Window(CTkToplevel):
    def __init__(self, warning, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.geometry("200x200")
        self.resizable(False,False)
        self.title("Warning!")
        self.mainframe = CTkFrame(self,fg_color = "white",bg_color='white')
        self.mainframe.place(relx = 0.5,rely = 0.5, relwidth = 1, relheight = 1)
        self.label = CTkLabel(self.mainframe,text = "warning",font = ('Lato',16),text_color=UBC_BLUE)
        self.label.place(relx=0.5,rely=0.4,relheight = 0.6,relwidth = 0.9,anchor = CENTER)
        self.okay = CTkButton(self.mainframe,text = "Okay", text_color="white", corner_radius=0,bg_color=UBC_BLUE,
                              fg_color=UBC_BLUE, hover_color=HOVER,command = self.okay_click)
        self.okay.place(relx = 0.5, rely = 0.5, relheight = 0.2, relwidth = 0.6,anchor = CENTER)
    
    def okay_click(self):
        self.destroy()

class Student_Choice_Frame(CTkFrame):
    def __init__(self,parent,main,width,height):
        super().__init__(parent,width = width,height = height,bg_color='white',fg_color='white')
        self.width = width
        self.height = height
        self.main = main
        self.student_frames = []
        self.headers = None
        self.table_ready = False
        

        self.refresh_btn = CTkButton(self,text = "Refresh",
                                     bg_color=HOVER,fg_color=HOVER,corner_radius=0,
                                     font = SMALL_FONT, command = self.update_table)
        self.refresh_btn.place(rely = 0, relx = 0, relwidth = 0.15, relheight = 0.1)
        self.select_all_btn = CTkButton(self,text = "Select All",
                                     bg_color=HOVER,fg_color=HOVER,corner_radius=0,
                                     font = SMALL_FONT, command = self.select_all)
        self.select_all_btn.place(rely = 0, relx = 0.15, relwidth = 0.2, relheight = 0.1)
        self.deselect_all_btn = CTkButton(self,text = "Deselect All",
                                     bg_color=HOVER,fg_color=HOVER,corner_radius=0,
                                     font = SMALL_FONT, command = self.deselect_all)
        self.deselect_all_btn.place(rely = 0, relx = 0.35, relwidth = 0.25, relheight = 0.1)
        self.search = CTkEntry(self,placeholder_text = "Search",
                                     bg_color=HOVER,fg_color='white',corner_radius=0,
                                     font = SMALL_FONT,placeholder_text_color=HOVER,
                                     text_color=UBC_BLUE,border_width=3,border_color=HOVER)
        self.search.place(rely = 0, relx = 0.6, relwidth = 0.4, relheight = 0.1)
        self.search.bind('<Return>',self.on_search_enter)
        self.search.bind('<Button-1>',self.on_search_click)


        self.disable_all()
        self.scroll_frame = CTkScrollableFrame(self, corner_radius = 0, fg_color='white',bg_color='white')
        self.scroll_frame.place(relx = 0, rely = 0.1, relwidth = 1, relheight = 0.9)
        
    def update_table(self):
        self.on_search_click('e')
        if self.table_ready:
            for frame in self.student_frames:
                frame['frame'].pack()
            return

        for frame in self.student_frames:
            frame['frame'].destroy()
        self.canvas = self.main.canvas
        source_course = self.canvas.get_course(self.main.source_course_id)
        destination_course = self.canvas.get_course(self.main.destination_course_id)
        
        if self.headers is None:
            self.headers = self.add_headers(self.scroll_frame,self.width,30)
    
        students_a = source_course.get_users(enrollment_type = ['student'])
        students_b = destination_course.get_users(enrollment_type = ['student'])
        
        cross_over_students = [student for student in students_a if student.id in [student.id for student in students_b]]

        for i, student in enumerate(cross_over_students):
            self.student_frames.append(self.add_student_frame(self.scroll_frame,student,self.width,30,i%2))

        self.table_ready = True

    def add_headers(self,parent,width,height):
        headers = CTkFrame(parent, width = width, height = height, 
                         corner_radius=0, fg_color='white', bg_color='blue')
        
        check_box = CTkLabel(headers, width = self.width * 0.15, height = self.width * 0.08,
                                fg_color='white', bg_color='white',text = "Select",font = ('Lato',18),text_color=UBC_BLUE,anchor = "w")
        check_box.place(relx = 0.05,rely = 0, relwidth = 0.15, relheight = 0.95)

        name_label = CTkLabel(headers,width = self.width * 0.5, height = 30, font = ('Lato',18), text = "Name",
                              text_color=UBC_BLUE, fg_color='white',bg_color='white',anchor='w')
        name_label.place(relx = 0.25, rely = 0, relwidth = 0.5, relheight = 1)

        student_num_label = CTkLabel(headers,width = self.width * 0.4, height = 30, font = ('Lato',18), text = "S#",
                              text_color=UBC_BLUE, fg_color='white',bg_color='white',anchor='w')
        student_num_label.place(relx = 0.75, rely = 0, relwidth = 0.4, relheight = 1)

        headers.pack()

        return headers

    def add_student_frame(self,parent,student,width,height,grey_or_white):
        if grey_or_white == 0:
            colour = "#dddddd"
        else:
            colour = "white"
        frame = CTkFrame(parent, width = width, height = height, 
                         corner_radius=0, fg_color=colour, bg_color=colour)
        
        

        check_box = CTkCheckBox(frame, width = self.width * 0.15, height = self.width * 0.08, checkbox_height=24,
                                checkbox_width=24,checkmark_color=HOVER,
                                fg_color=colour, bg_color=colour,text = "",hover_color = HOVER, hover = True,
                                corner_radius=0,border_color=HOVER,onvalue = 1, offvalue = 0)
        check_box.place(relx = 0.05,rely = 0, relwidth = 0.07, relheight = 0.95)
        check_box.select()

        line1 = CTkLabel(frame,text = "", corner_radius=0,fg_color=HOVER,bg_color=HOVER)
        line1.place(relx = 0.2,rely = 0,relheight = 1,relwidth = 0.002)

        name_label = CTkLabel(frame, font = self.font, text = student.name,
                              text_color=UBC_BLUE, fg_color=colour,bg_color=colour,anchor='w')
        name_label.place(relx = 0.25, rely = 0, relwidth = 0.45, relheight = 1)
        
        line2 = CTkLabel(frame,height = height,text = "", corner_radius=0,fg_color=HOVER,bg_color=HOVER)
        line2.place(relx = 0.7,rely = 0,relheight = 1,relwidth = 0.002)

        if hasattr(student,'sis_user_id'):
            if student.sis_user_id is not None:
                num = student.sis_user_id
            else:
                num = student.id
        else:
            num = student.id

        student_num_label = CTkLabel(frame,width = self.width * 0.4, height = 30, font = self.font, text = num,
                              text_color=UBC_BLUE, fg_color=colour,bg_color=colour,anchor='w')
        student_num_label.place(relx = 0.75, rely = 0, relwidth = 0.4, relheight = 1)

        frame.pack()

        return {'frame' : frame, 'check_box' : check_box, 'student' : student, 'student_num' : num}

    def select_all(self):
        for frame in self.student_frames:
            frame['check_box'].select()

    def deselect_all(self):
        for frame in self.student_frames:
            frame['check_box'].deselect()

    def on_search_click(self,event):
        self.search.delete(0,tk.END)

    def on_search_enter(self,event):
        self.main.focus()
        search = self.search.get()
        self.update_table()
        for frame in self.student_frames:
            if not (search in frame['student'].name or search == str(frame['student_num']) or search == str(frame['student'].id)):
                frame['frame'].pack_forget()

    def enable_all(self):
        self.refresh_btn.configure(state = "normal")
        self.select_all_btn.configure(state = "normal")
        self.deselect_all_btn.configure(state = "normal")
        self.search.configure(state = "normal")
    
    def disable_all(self):
        self.refresh_btn.configure(state = "disabled")
        self.select_all_btn.configure(state = "disabled")
        self.deselect_all_btn.configure(state = "disabled")
        self.search.configure(state = "disabled")
        self.table_ready = False
        for frame in self.student_frames:
            frame['frame'].destroy()
        if self.headers is not None:
            self.headers.destroy()
        self.headers = None

    def get_chosen_students(self):
        chosen_students = []
        for frame in self.student_frames:
            if frame['check_box'].get() == 1:
                chosen_students.append(frame['student'].id)
        return chosen_students

class Loading_Done_Window(CTkToplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.main = parent
        self.title("Finished")
        self.geometry("360x200")
        self.resizable(False,False)
        self.mainframe = CTkFrame(self,bg_color=UBC_BLUE,fg_color=UBC_BLUE)
        self.info = CTkLabel(self.mainframe,width=200,height=100,text="Loading...",text_color='white',
                             font = ('Lato',30,'bold'),wraplength = 400*0.75)
        self.info.place(relx = 0.5,rely=0.33,relwidth = 0.75,relheight = 0.3,anchor = CENTER)
        
        self.mainframe.place(relx=0.5,rely=0.5,relwidth=1,relheight=1,anchor=CENTER)

        self.link = CANVAS_URL

    def finished(self,link):
        self.info.configure(text = "Done!")
        self.link = link
        self.link_btn = CTkButton(self.mainframe,width = 150, height = 60, 
                                     corner_radius=0, text = "Open Assignment",
                                     command=self.open_link,bg_color='white',fg_color='white',
                                     hover_color=HOVER,font = ('Lato',16),text_color=UBC_BLUE)
        self.link_btn.place(x = 95, y = 200 - 20 - 30,anchor = CENTER)
        self.close_btn = CTkButton(self.mainframe,width = 150, height = 60, 
                                     corner_radius=0, text = "Exit",
                                     command=self.main.destroy,bg_color='white',fg_color='white',
                                     hover_color=HOVER,font = ('Lato',16),text_color=UBC_BLUE)
        self.close_btn.place(x = 360-95, y = 200 - 20 - 30,anchor = CENTER)

    def open_link(self):
        webbrowser.open(self.link)
        self.main.destroy()

class Documentation(CTkToplevel):
    def __init__(self,parent,index):
        super().__init__(parent)
        self.main = parent
        self.index = index

        self.resizable(False,False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        width = 800
        height = 650
        self.geometry(f"{width}x{height}")
        self.transient(self.main)
        self.focus()
        self.title("Submission Transfer App Documentation")

        tabview = CTkTabview(self,fg_color=UBC_BLUE,bg_color=UBC_BLUE,segmented_button_fg_color=UBC_BLUE,
                             segmented_button_selected_hover_color=LIGHT_BLUE,
                             segmented_button_unselected_hover_color=HOVER,
                             segmented_button_selected_color=HOVER,
                             segmented_button_unselected_color=UBC_BLUE,
                             corner_radius=0,text_color='white',
                             border_width=0,width = width, height = height - 80)
        tabview.pack(fill = BOTH)

        access_code_tab = tabview.add("Get Access Code")
        course_link = tabview.add("Get Course Link")
        assignment_link = tabview.add("Get Assignment Link")
        download_code_tab = tabview.add("Download Source Code")

        
        
        self.create_tab(course_link,'course_link.txt','Get Course Link')
        self.create_tab(assignment_link,'assignment_link.txt','Get Assignment Link')
        
        self.create_download_tab(download_code_tab)
        self.create_access_code_tab(access_code_tab)

        tabview._segmented_button._buttons_dict['Get Access Code'].configure(width = 160, height = 40,font = ('Lato',16))
        tabview._segmented_button._buttons_dict['Get Course Link'].configure(width = 160, height = 40,font = ('Lato',16))
        tabview._segmented_button._buttons_dict['Get Assignment Link'].configure(width = 200, height = 40,font = ('Lato',16))
        tabview._segmented_button._buttons_dict['Download Source Code'].configure(width = 220, height = 40,font = ('Lato',16))


        tabs = ["Get Access Code","Get Course Link","Get Assignment Link","Download Source Code"]
        tabview.set(tabs[self.index])

        bottom_frame = CTkFrame(self,fg_color=UBC_BLUE,bg_color=UBC_BLUE)
        bottom_frame.pack(fill = BOTH)

        close = CTkButton(bottom_frame,width = 200, height = 60, text = "Close", font = BIG_FONT, text_color=UBC_BLUE,
                          fg_color='white',bg_color='white',hover_color=HOVER,command = self.on_closing,
                          corner_radius=0)
        close.pack(pady = (0,20), padx = 20, side = RIGHT)
        

    def create_access_code_tab(self,parent):
        header = CTkLabel(parent, fg_color = UBC_BLUE,bg_color=UBC_BLUE,corner_radius=0,
                          text = 'Get Access Code', font = ('Lato',30),text_color='white',anchor='w')
        header.pack(padx = 20, pady = (20,10),fill = X)

        scrollable = CTkScrollableFrame(parent, fg_color='white',bg_color='white',
                                        corner_radius=0,scrollbar_button_color=UBC_BLUE,
                                        scrollbar_button_hover_color=HOVER)
        scrollable.pack(padx=20,pady = (0,20),fill = BOTH,expand = True)
        words1 = CTkLabel(scrollable,fg_color='white',bg_color='white',text_color=UBC_BLUE,
                           font = ('Lato',16),text = "1.  Go to your Canvas. Click on 'Account' in the left sidebar. Then, click on 'Settings'.",
                           justify = 'left',anchor = 'w',wraplength=600)
        words1.pack(padx = 20, pady = 20,fill = BOTH,expand = True)

        self.add_image("access_code_1",scrollable)

        words2 = CTkLabel(scrollable,fg_color='white',bg_color='white',text_color=UBC_BLUE,
                           font = ('Lato',16),text = "2.  On the settings page, scroll down (it may take a while) until you see '+ New Access Token'. Click this button.",
                           justify = 'left',anchor = 'w',wraplength=600)
        words2.pack(padx = 20, pady = 20,fill = BOTH,expand = True)

        self.add_image("access_code_2",scrollable)

        words3 = CTkLabel(scrollable,fg_color='white',bg_color='white',text_color=UBC_BLUE,
                           font = ('Lato',16),text = "3.  The popup 'Generate an Access Token' should appear. In the purpose, fill in 'transferring canvas assignments or a similar reason. The expiration date can be blank. Then click 'Generate Token'. ",
                           justify = 'left',anchor = 'w',wraplength=600)
        words3.pack(padx = 20, pady = 20,fill = BOTH,expand = True)

        self.add_image("access_code_3",scrollable)

        words4 = CTkLabel(scrollable,fg_color='white',bg_color='white',text_color=UBC_BLUE,
                           font = ('Lato',16),text = "4.  An 'Access Token Details' pop up should appear. Copy the long string of letters and numbers appearing after 'Token' at the top of the pop up. Paste this somewhere private and secure, as you will not have access to see it again once this window is closed.",
                           justify = 'left',anchor = 'w',wraplength=600)
        words4.pack(padx = 20, pady = 20,fill = BOTH,expand = True)

        self.add_image("access_code_4",scrollable)

        words5 = CTkLabel(scrollable,fg_color='white',bg_color='white',text_color=UBC_BLUE,
                           font = ('Lato',16),text = "5.  Open notepad on your computer and create a new text file. Paste your access code into a text file name save the file. Open the file when prompted by the app.",
                           justify = 'left',anchor = 'w',wraplength=600)
        words5.pack(padx = 20, pady = 20,fill = BOTH,expand = True)

    def create_tab(self,parent,file_name,name):
        with open(self.main.resource_path(file_name),'r') as file:
            text = file.read()
        
        header = CTkLabel(parent, fg_color = UBC_BLUE,bg_color=UBC_BLUE,corner_radius=0,
                          text = name, font = ('Lato',30),text_color='white',anchor='w')
        header.pack(padx = 20, pady = (20,10),fill = X)

        scrollable = CTkScrollableFrame(parent, fg_color='white',bg_color='white',
                                        corner_radius=0,scrollbar_button_color=UBC_BLUE,
                                        scrollbar_button_hover_color=HOVER)
        scrollable.pack(padx=20,pady = (0,20),fill = BOTH,expand = True)
        words = CTkLabel(scrollable,fg_color='white',bg_color='white',text_color=UBC_BLUE,
                           font = ('Lato',16),text = text,justify = 'left',anchor = 'w')
        words.pack(padx = 20, pady = 20,fill = BOTH,expand = True)

        self.add_image(name,scrollable)

    def add_image(self,name,frame):
        try:
            image = Image.open(self.main.resource_path(name + ".png"))
            width, height = image.size
            image = CTkImage(light_image = image,size = (400,height/width * 400))
        except (FileNotFoundError, tk.TclError):
            print(f"No file found: {name}.png")
        else:
            label = CTkLabel(frame, image = image,text="",width = 400, height = height/width * 400)
            label.pack(pady=20)

    def create_download_tab(self,frame):
        text = CTkLabel(frame, text = "Download the code from below. \n\nLibraries used include: CTkinter, Tkinter, PIL, \nCanvasAPI, re, and webbrowser.",
                        font = ('Lato',30),text_color='white',width = 300, height = 50)
        text.pack(padx = 20, pady = (50,20))

        download_btn = CTkButton(frame, fg_color='white',bg_color='white',corner_radius=0,
                                 width = 300, height = 150, text = "Download Code", font = ('Lato',30),
                                 hover_color = LIGHT_BLUE, command = self.download_code,text_color=UBC_BLUE)
        download_btn.pack(padx = 20, pady = 20)

        credits = CTkLabel(frame, text = "Developed by Chrisotopher Elwell, \nwith help from Steven Louie and Ayla Cilliers\nUBC APSC CIS 2024", anchor='center',
                           font = ('Lato',16),text_color='white',width = 300, height = 50)
        credits.pack(padx = 20, pady = (50,20))

    def download_code(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if save_path:
            with open(self.resource_path('code_base.txt'), 'r') as file:
                file_content = file.read()
            
            with open(self.resource_path(save_path), 'w') as file:
                file.write(file_content)
    
    def on_closing(self):
        self.main.docs = None
        if self.index == 0 and self.main.get_token_window is not None:
            self.main.get_token_window.grab_set()
        self.destroy()

if __name__ == "__main__":
    app = main_app()
    app.mainloop()