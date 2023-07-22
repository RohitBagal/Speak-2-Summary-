import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import speech_recognition as sr
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openai
import textwrap

# Set your ChatGPT API key here
openai.api_key = "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"

def show_popup_message(title, message, message_type=tk.messagebox.INFO):
    messagebox.showinfo(title, message, icon=message_type)

def initialize_speech_recognition():
    recognizer = sr.Recognizer()
    return recognizer

def capture_audio(recognizer, subtitles_label, start_button, stop_button, download_button, stop_event, subtitles_list):
    start_button.config(state=tk.DISABLED)  # Disable the "Start" button
    download_button.config(state=tk.DISABLED)  # Disable the "Download" button while capturing
    subtitles_label.config(text="Recording in progress...")  # Update the subtitles label
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while not stop_event.is_set():
            audio_data = recognizer.listen(source)

            try:
                # Convert audio to text using the recognizer
                text = recognizer.recognize_google(audio_data)
                # Append the recognized text to the subtitles list
                subtitles_list.append(text)
                # Update the GUI with the text (e.g., add it to the subtitles panel)
                cumulative_text = "\n".join(subtitles_list)
                subtitles_label.config(text=cumulative_text)  # Update the subtitles label
            except sr.UnknownValueError:
                subtitles_label.config(text="Couldn't understand the audio.")
            except sr.RequestError as e:
                subtitles_label.config(text="Error occurred while processing the audio.")

    subtitles_label.config(text="Audio capture stopped. You can download the summary now.")  # Update the subtitles label
    start_button.config(state=tk.NORMAL)  # Enable the "Start" button after stopping
    download_button.config(state=tk.NORMAL)  # Enable the "Download" button after stopping
    stop_button.config(state=tk.DISABLED)  # Disable the "Stop" button after stopping

def start_capture(subtitles_label, start_button, stop_button, download_button, subtitles_list):
    stop_event.clear()
    threading.Thread(target=capture_audio, args=(recognizer, subtitles_label, start_button, stop_button, download_button, stop_event, subtitles_list)).start()
    start_button.config(state=tk.DISABLED)  # Disable the "Start" button after starting
    stop_button.config(state=tk.NORMAL)  # Enable the "Stop" button after starting

def stop_capture():
    stop_event.set()

def generate_summary(subtitles_list):
    # Concatenate the subtitles into a single string for summarization
    input_text = "Summerize the following in simple words \n".join(subtitles_list)
    # Set the model and parameters for the summarization
    model = "text-davinci-003"
    response = openai.Completion.create(
        engine=model,
        prompt=input_text,
        temperature=0.7,
        max_tokens=100
    )
    summary = response.choices[0].text.strip()
    return summary

def save_captions_to_pdf(subtitles_list, summary):
    pdf_filename = "captions_with_summary.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)

    # Set up the font size and position for the captions and summary
    font_size = 12
    x_pos = 50
    y_pos = 750

    # Write the "Captions" heading to the PDF
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x_pos, y_pos, "Captions:")
    y_pos -= 20

    # Write the original captions to the PDF
    for caption in subtitles_list:
        wrapped_captions = textwrap.fill(caption, width=60)
        for line in wrapped_captions.split("\n"):
            c.setFont("Helvetica", font_size)
            c.drawString(x_pos, y_pos, line)
            y_pos -= 20  # Move to the next line for the next caption

    # Update the y_pos for the "Summary" heading
    y_pos -= 30

    # Write the "Summary" heading to the PDF
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x_pos, y_pos, "Summary:")
    y_pos -= 20

    # Write the summary to the PDF
    wrapped_summary = textwrap.fill(summary, width=60)
    for line in wrapped_summary.split("\n"):
        c.setFont("Helvetica", font_size)
        c.drawString(x_pos, y_pos, line)
        y_pos -= 20

    c.save()

def download_captions(subtitles_label, subtitles_list):
    summary = generate_summary(subtitles_list)
    save_captions_to_pdf(subtitles_list, summary)
    download_button.config(state=tk.NORMAL)  # Enable the "Download" button after the PDF is saved
    show_popup_message("Captions Downloaded", "Captions and summary saved to PDF.", tk.messagebox.INFO)

def initialize_gui():
    app = tk.Tk()
    app.title("Speak 2 Summary")

    # Set ttkthemes style for the GUI (we use the "clam" theme)
    style = ttk.Style()
    style.theme_use("clam")  # Choose the "clam" theme (you can try other themes as well)

    # Add a header (logo or title) at the top
    header_label = tk.Label(app, text="Audio-to-Subtitles", font=("Arial", 20), padx=20, pady=10)
    header_label.pack()

    # Create a label to show the subtitles
    subtitles_list = []  # List to store recognized text from different audio segments
    subtitles_label = tk.Label(app, text="Subtitles will appear here", font=("Helvetica", 16), wraplength=400)
    subtitles_label.pack(padx=20, pady=20)

    # Create icons for buttons (not actual icons, just for demonstration)
    start_icon = tk.Label(app, text="▶", font=("Arial", 14))
    stop_icon = tk.Label(app, text="■", font=("Arial", 14))
    download_icon = tk.Label(app, text="⬇", font=("Arial", 14))

    # Create "Start," "Stop," and "Download" buttons
    start_button = ttk.Button(app, text="Start", command=lambda: start_capture(subtitles_label, start_button, stop_button, download_button, subtitles_list))
    start_button.pack(side=tk.LEFT, padx=10, pady=5)
    start_icon.pack(side=tk.LEFT, padx=5)  # Add the start icon

    stop_button = ttk.Button(app, text="Stop", command=stop_capture, state=tk.DISABLED)  # Disable the "Stop" button initially
    stop_button.pack(side=tk.LEFT, padx=10, pady=5)
    stop_icon.pack(side=tk.LEFT, padx=5)  # Add the stop icon

    global download_button
    download_button = ttk.Button(app, text="Download", command=lambda: download_captions(subtitles_label, subtitles_list), state=tk.DISABLED)  # Disable the "Download" button initially
    download_button.pack(side=tk.LEFT, padx=10, pady=5)
    download_icon.pack(side=tk.LEFT, padx=5)  # Add the download icon

    app.mainloop()

if __name__ == "__main__":
    recognizer = initialize_speech_recognition()
    stop_event = threading.Event()
    initialize_gui()
