import sqlite3
import threading
import time
import tkinter as tk
import speech_recognition as sr
from tkinter import Canvas, filedialog, messagebox, ttk, PhotoImage
from tkinter import filedialog
from PIL import ImageTk, Image
import os
import sqlite3
import numpy as np
import scipy.signal as signal
import wave
from pydub import AudioSegment

# Create a tkinter window frame
window = tk.Tk()
window.title("SPEECH RECOGNITION APP")
window.configure(bg="slategrey")
window.state("zoomed")
button_padding = {"padx": 10, "pady": 5}

#Create a header canvas object
canvas= Canvas (window, width= 1000, height= 130, bg="antiquewhite", highlightthickness=0)

#Add a text in header Canvas
canvas.create_text(500, 30, text="SPEECH RECOGNITION APP", fill="black", font=('Helvetica 30 bold'))
canvas.create_text(500, 80, text="Speak. We transcribe.", fill="black", font=('Helvetica 13'))
canvas.create_text(500, 110, text="Effortlessly convert your speech to text with our accurate and advanced technology.", fill="black", font=('Helvetica 13'))
canvas.place(relx=0.5, rely=0.12, anchor='center')

# Create a footer canvas object
footer_canvas = tk.Canvas(window, width=300, height=20, bg="antiquewhite", highlightthickness=0)

# Add text to the footer canvas
footer_canvas.create_text(150, 12, text="© 2023 Speech Recognition App. All rights reserved.", fill="black", font=('Helvetica 8'))

# Pack the footer canvas
footer_canvas.place(relx=0.5, rely=0.96, anchor='center')

# Create a canvas object for user input fields
input_canvas = tk.Canvas(window, width=500, height=500, bg="antiquewhite", highlightthickness=0)
input_canvas.place(x=110, y=180)
input_canvas.create_text(250, 30, text="To transcribe, kindly fill this form", fill='black', font=('Helvetica 13'))

# Create user input fields
user_name_label = tk.Label(input_canvas, text="Enter your First name:", padx=10, pady=10, font=('Helvetica 10 bold'), bg="#FF7F50")
user_name_label_window = input_canvas.create_window(50, 100, anchor='nw', window=user_name_label)
user_name_entry1 = tk.Entry(input_canvas, width=30, font=('Helvetica 10 bold'))
user_name_entry_window = input_canvas.create_window(270, 120, anchor='nw', window=user_name_entry1)

user_name_label = tk.Label(input_canvas, text="Enter your Second name:", padx=10, pady=10, font=('Helvetica 10 bold'), bg="#FF7F50")
user_name_label_window = input_canvas.create_window(50, 230, anchor='nw', window=user_name_label)
user_name_entry2 = tk.Entry(input_canvas, width=30, font=('Helvetica 10 bold'))
user_name_entry_window = input_canvas.create_window(270, 250, anchor='nw', window=user_name_entry2)

user_email_label = tk.Label(input_canvas, text="Enter your email address:", padx=10, pady=10, font=('Helvetica 10 bold'), bg="#FF7F50")
user_email_label_window = input_canvas.create_window(50, 360, anchor='nw', window=user_email_label)
user_email_entry = tk.Entry(input_canvas, width=30, font=('Helvetica 10 bold'))
user_email_entry_window = input_canvas.create_window(270, 380, anchor='nw', window=user_email_entry)


# Function to apply Fourier Transform and Wiener Filtering to audio data
def apply_noise_filter(audio):
    # Convert AudioSegment to array of samples
    samples = np.array(audio.get_array_of_samples())

    # Apply Fourier Transform to audio data
    spectrum = np.fft.fft(samples)
    freq = np.fft.fftfreq(len(samples))

    # Compute power spectral density (PSD) and noise spectral density (NSD)
    psd = np.abs(spectrum)**2 / len(samples)
    nsd = np.mean(psd[:len(psd)//2])

    # Compute Wiener filter coefficients
    wiener = np.maximum(0, psd - nsd) / np.maximum(psd, nsd)

    # Apply Wiener filter to audio data
    filtered_samples = np.fft.ifft(wiener * spectrum).real

    # Convert array of samples back to AudioSegment
    filtered_audio = AudioSegment(filtered_samples.tobytes(), frame_rate=audio.frame_rate, sample_width=audio.sample_width, channels=audio.channels)
    return filtered_audio

# Function to upload audio file and transcribe it
def upload_and_transcribe():
    # Open file dialog to select an audio file
    filepath = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav;*.mp3")])
    
    # Use SpeechRecognition library to transcribe audio
    r = sr.Recognizer()
    with sr.AudioFile(filepath) as source:
        audio_data = r.record(source)
        
    # Convert AudioData to AudioSegment
    audio = AudioSegment(audio_data.frame_data, frame_rate=audio_data.sample_rate, sample_width=audio_data.sample_width, channels=getattr(audio_data, 'channels', 1))

    # Apply noise filter to audio data
    audio = apply_noise_filter(audio)
        
    # Transcribe filtered audio
    transcript = r.recognize_google(audio_data)

    # get user info from user input
    first_name = user_name_entry1.get()
    second_name = user_name_entry2.get()
    email = user_email_entry.get()

    # Display transcript in a new window
    transcript_window = tk.Toplevel(window)
    transcript_window.title("Transcription Result")
    transcript_window.geometry("800x600")
    transcript_window.configure(bg='#F0E68C')

    # Add header label
    tk.Label(transcript_window, text="Transcription Results: Your Audio File Transcript", bg='#F0E68C', fg='black', font=('Helvetica', 16, 'bold'), pady=20).pack()

    # Add transcript label
    transcript_label = tk.Label(transcript_window, text=transcript, bg='antiquewhite', font=('Helvetica', 13), padx=30, pady=30, width=200, height=15)
    transcript_label.pack()

    # Insert transcript and user data into database
    def save_transcript():
        push_to_database(transcript, first_name, second_name, email)
        transcript_label.configure(text="Transcription saved to database.")
        save_button.configure(state="disabled")

    save_button = tk.Button(transcript_window, text="Save Transcript", command=save_transcript, font=("Helvetica", 13))
    save_button.pack(padx=20, pady=30)

# Function to push data to database
def push_to_database(transcript, first_name, second_name, email):
    # Connect to SQLite database
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute("CREATE TABLE IF NOT EXISTS transcripts (id INTEGER PRIMARY KEY AUTOINCREMENT, transcript TEXT, first_name TEXT, second_name TEXT, email TEXT)")

    # Insert transcript and user data into database
    c.execute("INSERT INTO transcripts (transcript, first_name, second_name, email) VALUES (?, ?, ?, ?)", (transcript, first_name, second_name, email))

    # Commit changes and close connection
    conn.commit()
    conn.close()

def timer(record_button):
    timer_seconds = 5
    while timer_seconds > 0:
        timer_seconds -= 1
        time.sleep(1)
    record_button.config(state="normal")

# Function to record audio and transcribe it
def record_and_transcribe(record_button):
    # Initialize SpeechRecognition library
    r = sr.Recognizer()

    # Create a thread for the timer
    record_button.config(state="disabled")
    timer_thread = threading.Thread(target=timer, args=(record_button,))
    timer_thread.start()

    # Create a window for displaying the transcription
    transcription_window = tk.Toplevel(window)
    transcription_window.title("Transcription")
    transcription_window.geometry("800x600")
    transcription_window.configure(bg='#F0E68C')

    # Create a label for the header
    transcription_header = tk.Label(transcription_window, text="Transcribe your voice to text by hitting the record button below", font=("Helvetica", 10), bg='#F0E68C')
    transcription_header.pack(pady=50)

    # Create a label for displaying the transcription
    transcription_label = tk.Label(transcription_window, text="", font=("Helvetica 15"))
    transcription_label.pack(pady=100, padx=100)

    # Define function to insert transcript and user data into database
    def save_transcript():
        push_to_database(transcription_label.cget("text"), user_name_entry1.get(), user_name_entry2.get(), user_email_entry.get())
        messagebox.showinfo("Success", "Transcription saved to database.")
        save_button.config(state="disabled")

    # Create a button for saving the transcription
    save_button = tk.Button(transcription_window, text="Save Transcript", command=save_transcript)
    save_button.pack(side="bottom", anchor="s", pady=20, padx=40)  
    
    # Function to start recording
    def start_recording():

        # Start the timer thread
        global running, elapsed_time
        running = True
        elapsed_time = 0
        timer_thread = threading.Thread(target=timer, args=(record_button,))
        timer_thread.start()

        update_timer_thread = threading.Thread(target=update_timer)
        update_timer_thread.start()

        # get user info from user input
        first_name = user_name_entry1.get()
        second_name = user_name_entry2.get()
        email = user_email_entry.get()

        # Use the microphone as source
        with sr.Microphone() as source:
            # Adjust for ambient noise
            r.adjust_for_ambient_noise(source)

            # Display recording message
            transcription_label.config(text="Recording...")

            # Listen for user input
            audio = r.listen(source)

             # Transcribe user input
            try:
                transcription = r.recognize_google(audio)
                transcription_label.config(text=transcription)

            except sr.UnknownValueError:
                transcription_label.config(text="Unable to recognize speech")
            except sr.RequestError as e:
                transcription_label.config(text="Error: {0}".format(e))

    # Function to stop recording
    def stop_recording():
        # Stop the timer thread
        global timer_running
        timer_running = False

    # Function to update timer label
    def update_timer():
        global timer_running
        timer_running = True
        start_time = time.time()
        while timer_running:
            elapsed_time = time.time() - start_time
            timer_label.config(text="Time: {:.2f}s".format(elapsed_time))
            time.sleep(0.1)

    # Create a label for displaying the timer
    timer_label = tk.Label(transcription_window, text="Time: 0.00s", font=("Helvetica 15"))
    timer_label.pack()

    # Create custom styles for the buttons
    style = ttk.Style()
    style.configure('Green.TButton', foreground='green')
    style.configure('Red.TButton', foreground='red')

    # Create start and stop recording buttons
    start_button = ttk.Button(transcription_window, text="Start Recording", style='Green.TButton', command=start_recording)
    start_button.pack(pady=20, padx=10)

    stop_button = ttk.Button(transcription_window, text="Stop Recording", style='Red.TButton', command=stop_recording)
    stop_button.pack(pady=20, padx=10)

    # Start timer thread
    timer_thread = threading.Thread(target=update_timer)

# Create a canvas for the buttons
button_canvas = tk.Canvas(window, width=500, height=500, bg="antiquewhite", highlightthickness=0)
button_canvas.place(x=800, y=180)

button_canvas.create_text(250, 30, text="Please choose from the following options.", fill='black', font=('Helvetica 13'))


# Add buttons to the canvas
button1 = tk.Button(button_canvas, text="Select Audio File to Transcribe", font=("Helvetica 15"), command=upload_and_transcribe, padx=10, pady=10, bg="#FF7F50")
button_canvas.create_window(250, 130, window=button1)

record_button = tk.Button(button_canvas, text="Record Audio to Transcribe", font=("Helvetica 15"), command=lambda: record_and_transcribe(record_button), padx=10, pady=10, bg="#FF7F50")
button_canvas.create_window(250, 260, window=record_button)

button3 = tk.Button(button_canvas, text="Save", font=("Helvetica 15"), command=push_to_database, padx=10, pady=10, bg="#FF7F50")
button_canvas.create_window(250, 390, window=button3)

# Start tkinter mainloop
window.mainloop()
