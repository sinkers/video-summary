import pysrt
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")


def get_duration_ms(fps, frame_count):
    if frame_count == 0:
        return 0
    duration_frame = 1000.0 / fps
    return frame_count * duration_frame

def srt_get_time_range(srt_file, start_time, end_time):
   subs = pysrt.open(srt_file )
   return_text = ""

   # Note it looks like the transcription will have duplicate text for a particular time range
   # Likely
   for sub in subs:
       if sub.start > start_time and sub.start < end_time:
           return_text += sub.text
           #print("%s %s" % (sub.start, sub.text))
   return return_text






