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


# This is just here for testing purposes at the moment needs to be broken out
def main():
    start = pysrt.SubRipTime(hours=0, minutes=1, seconds=45)
    end = pysrt.SubRipTime(hours=0, minutes=6, seconds=30)
    print(start)
    text = srt_get_time_range("files/allhands_subtitles.srt",start, end)
    print(text)
    print("Words: %d" % len(text.split(" ")))

    print(get_chatgpt_summary(text))

