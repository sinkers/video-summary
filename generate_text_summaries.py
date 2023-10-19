import openai
import pysrt
import glob
import os
import helpers
from PIL import Image, ImageDraw, ImageFont
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import sys
from utils import convert_slides_to_pdf

# Download the NLTK data for tokenization if you haven't already
nltk.download('punkt')

# Read a directory of images
# Look at the frame counts from the image names

def get_chatgpt_summary(text):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        messages=[
            { 
                "role": "user", 
                "content": f"Summarize this into 5 dot points: {text}"
            }
            ],
        temperature=0,
        max_tokens=256
    )

def ms_to_hh_mm_ss(duration_ms):
    seconds, milliseconds = divmod(duration_ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, milliseconds)

def ms_to_hh_mm_ss_tuple(duration_ms):
    seconds, milliseconds = divmod(duration_ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return (hours, minutes, seconds, milliseconds)

def extract_first_1_to_4_numbers(s):
    # Initialize an empty string to accumulate the digits
    digits = ""
    for char in s:
        if char.isdigit() and len(digits) < 4:
            digits += char
        elif digits:
            break  # Stop once we've collected 4 digits or if no more digits are found
    return int(digits)

def split_text_into_blocks(text, block_size=500):
    words = text.split()
    blocks = []
    current_block = []

    for word in words:
        current_block.append(word)

        if len(current_block) >= block_size:
            blocks.append(" ".join(current_block))
            current_block = []

    if current_block:
        blocks.append(" ".join(current_block))

    return blocks

def split_text_into_blocks_nltk(text, block_size=500):
    sentences = sent_tokenize(text)  # Tokenize text into sentences
    blocks = []
    current_block = []

    for sentence in sentences:
        words = word_tokenize(sentence)  # Tokenize each sentence into words
        if len(current_block) + len(words) <= block_size:
            current_block.extend(words)
        else:
            blocks.append(" ".join(current_block))
            current_block = words

    # Add the last block if it's not empty
    if current_block:
        blocks.append(" ".join(current_block))

    return blocks

def read_files(image_dir):
    files = glob.glob(os.path.join(image_dir,"*.png"))
    files = sorted(files, key=extract_first_1_to_4_numbers)
    slide_index = 0
    for f in files:
        print(os.path.basename(f))
        # Files are scene_framestart-frameend
        scene = os.path.basename(f).split("_")
        start_frame = scene[1].split("-")[0]
        end_frame = os.path.splitext(scene[1].split("-")[1])[0]
        frame_duration = int(end_frame) - int(start_frame)
        start_time = helpers.get_duration_ms(29.97, float(start_frame))
        end_time = helpers.get_duration_ms(29.97, float(end_frame))
        start_time_format = ms_to_hh_mm_ss(start_time)
        end_time_format = ms_to_hh_mm_ss(end_time)
        duration_format = ms_to_hh_mm_ss(helpers.get_duration_ms(29.97, float(frame_duration)))
        print(start_time_format)
        print("scene %s start frame: %s (%s) end frame: %s (%s) - Duration %s" % (scene[0], start_frame, start_time_format, end_frame, end_time_format, duration_format))

        # Extract from the subtitles
         
        end_time_format = ms_to_hh_mm_ss(end_time)
        hours, mins, secs, _ = ms_to_hh_mm_ss_tuple(start_time)
        start = pysrt.SubRipTime(hours=hours, minutes=mins, seconds=secs)
        hours, mins, secs, _ = ms_to_hh_mm_ss_tuple(end_time)
        end = pysrt.SubRipTime(hours=hours, minutes=mins, seconds=secs)
        text = helpers.srt_get_time_range("files/allhands_subtitles.srt",start, end)
        print("Text length: %d" % len(text.split(" ")))
        # Could get clever here and just append prior text
        # Even better would be to do some analysis e.g. look at nltk

        # We will only generate a slide if it is > 300 words
        if len(text.split(" ")) > 100:
              if len(text.split(" ")) > 500:
                # Split
                blocks = split_text_into_blocks_nltk(text)
                for block in blocks:
                    #print("*******\n")
                    #(print(block))
                    summary = get_chatgpt_summary(block)
                    output_file = os.path.join(image_dir, "%s_text_slide_%d.png" % (scene[0], slide_index))
                    slide_index += 1
                    generate_slide(summary["choices"][0]["message"]["content"], output_file)
                    #sys.exit()
                    
              else:
                summary = get_chatgpt_summary(text)
                output_file = os.path.join(image_dir, "%s_text_slide_%d.png" % (scene[0], slide_index))
                slide_index += 1
                generate_slide(summary["choices"][0]["message"]["content"], output_file)

        # If it is > 500 we will split into 500 word blocks

    return

def generate_slide(dot_point_text, output_file):
    dot_data = []
    y = 100
    for line in dot_point_text.split("\n"):
        dot_data.append({"position": (100, y), "text":line})
        y+=100
        print(line)
    # Open an existing image or create a new one
    #image = Image.open("your_image.png")  # Replace "your_image.png" with the path to your image
    image = Image.new(mode="RGB", size=(1920,1080))

    # Create a drawing object
    draw = ImageDraw.Draw(image)

    # Define the positions and text for the dot points
    #dot_data = [
    #    {"position": (100, 100), "text": "This is point 1. It has some long text that will wrap."},
    ##    {"position": (100, 200), "text": "Point 2"},
    #    {"position": (100, 300), "text": "Point 3"},
    #    {"position": (100, 400), "text": "Point 4"},
    #    {"position": (100, 500), "text": "Point 5"},
    #]

    # Set the size and color for the dots
    dot_size = 5
    dot_color = (255, 255, 255)  # RGB color (red in this example)

    # Define the font and size for the text
    #font = ImageFont.load_default()
    font = ImageFont.truetype("Arial.ttf", size=24)
    font_size = 36
    font_color = (255, 255, 255)  # RGB color (black)

    # Draw the dots and text on the image
    for dot in dot_data:
        x, y = dot["position"]
        text = dot["text"]
        
        # Draw the dot
        #draw.ellipse((x - dot_size, y - dot_size, x + dot_size, y + dot_size), fill=dot_color)

        # Possible options to draw nicer text
        # https://www.blog.pythonlibrary.org/2021/02/02/drawing-text-on-images-with-pillow-and-python/
        
        # Draw the text with word wrapping
        lines = []
        line = ""
        for word in text.split():
            if font.getsize(line + word)[0] <= image.width:
                line += word + " "
            else:
                lines.append(line)
                line = word + " "
        lines.append(line)
        
        y_text = y + dot_size + 5  # Adjust the vertical position for text
        for line in lines:
            draw.text((x, y_text), line, font=font, fill=font_color)
            y_text += font.getsize(line)[1]

    # Save or display the modified image
    image.save(output_file)  # Save the modified image as "output_image.png"
    #image.show()  # Display the modified image



# This is just here for testing purposes at the moment needs to be broken out
def main():
    read_files("files/output/allhands/KNN")
    convert_slides_to_pdf("files/allhands.mp4", "files/output/allhands/KNN")
    #generate_slide("bla")
    #start = pysrt.SubRipTime(hours=0, minutes=1, seconds=45)
    #end = pysrt.SubRipTime(hours=0, minutes=6, seconds=30)
    #print(start)
    ##text = srt_get_time_range("files/allhands_subtitles.srt",start, end)
    #print(text)
    #print("Words: %d" % len(text.split(" ")))

    #print(get_chatgpt_summary(text))

main()