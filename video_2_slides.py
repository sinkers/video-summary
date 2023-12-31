import os
import time
import sys
import cv2
import dlib
import argparse
from frame_differencing import capture_slides_frame_diff
from post_process import remove_duplicates
from utils import resize_image_frame, create_output_directory, convert_slides_to_pdf
import helpers


# -------------- Initializations ---------------------

FRAME_BUFFER_HISTORY = 15   # Length of the frame buffer history to model background.
DEC_THRESH = 0.90           # Threshold value, above which it is marked foreground, else background.
DIST_THRESH = 100           # Threshold on the squared distance between the pixel and the sample to decide whether a pixel is close to that sample.

MIN_PERCENT = 0.25         # %age threshold to check if there is motion across subsequent frames
MAX_PERCENT = 0.01          # %age threshold to determine if the motion across frames has stopped.

# ----------------------------------------------------


def capture_slides_bg_modeling(video_path, output_dir_path, type_bgsub, history, threshold, MIN_PERCENT_THRESH, MAX_PERCENT_THRESH):

    print(f"Using {type_bgsub} for Background Modeling...")
    print('---'*10)

   
    if type_bgsub == 'GMG':
        bg_sub = cv2.bgsegm.createBackgroundSubtractorGMG(initializationFrames=history, decisionThreshold=threshold)

    elif type_bgsub == 'KNN':
        bg_sub = cv2.createBackgroundSubtractorKNN(history=history, dist2Threshold=threshold, detectShadows=False) 
        

    capture_frame = False
    screenshots_count = 0

    # Capture video frames.
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("Source fps %.3f" % fps)

    if not cap.isOpened():
        print('Unable to open video file: ', video_path)
        sys.exit()
     
    
    start = time.time()
    frame_count = 0
    last_scene_start = 0

    # initialize face classifier & tracker
    cv2_data_dir = os.path.join(os.path.dirname(os.path.abspath(cv2.__file__)), 'data')
    face_cascade = cv2.CascadeClassifier(os.path.join(cv2_data_dir, 'haarcascade_frontalface_default.xml'))
    print('Using default frontalface Haar Cascade pre-loaded model.')
    tracker = dlib.correlation_tracker()
    trackingFace = False

    # Loop over subsequent frames.
    while cap.isOpened():
        
        ret, frame = cap.read()

        if not ret:
            break
        
        
        # Create a copy of the original frame.
        orig_frame = frame.copy() 
        # Resize the frame keeping aspect ratio.
        frame = resize_image_frame(frame, resize_width=640)

        # Apply each frame through the background subtractor.
        fg_mask = bg_sub.apply(frame)

        # For demo purposes write out the bg subtractions
        #png_filename = f"{frame_count:04}.png"
        #out_file_path = os.path.join(output_dir_path, png_filename)
        #cv2.imwrite(out_file_path, fg_mask)

        # Compute the percentage of the Foreground mask."
        p_non_zero = (cv2.countNonZero(fg_mask) / (1.0 * fg_mask.size)) * 100

        # %age of non-zero pixels < MAX_PERCENT_THRESH, implies motion has stopped.
        # Therefore, capture the frame.
        if p_non_zero < MAX_PERCENT_THRESH and not capture_frame:

            # Create greyscale version of frame for face tracking
            # Tracking example pulled from: https://www.guidodiepen.nl/2017/02/detecting-and-tracking-a-face-with-python-and-opencv/
            # Improvement opportunity #1: perform face detection on resized frame? (tried but worse results)
            grey = cv2.cvtColor(orig_frame, cv2.COLOR_BGR2GRAY)

            # If we're not tracking a face, look for one
            if not trackingFace:

                # Improvement opportunity #2: optimize scale factor (2nd arg in detectMultiScale)
                # Improvement opportunity #3: optimize minNeighbors (3rd arg in detectMultiScale)
                # From https://www.bogotobogo.com/python/OpenCV_Python/python_opencv3_Image_Object_Detection_Face_Detection_Haar_Cascade_Classifiers.php
                # "Higher value results in less detections but with higher quality."
                faces = face_cascade.detectMultiScale(grey, 1.05, 3)

                # if we find faces
                if len(faces) > 0:
                    x = 0
                    y = 0
                    w = 0
                    h = 0
                    maxArea = 0
                    for (_x, _y, _w, _h) in faces:
                        if _w * _h > maxArea:
                            x = int(_x)
                            y = int(_y)
                            w = int(_w)
                            h = int(_h)
                            maxArea = w * h

                        # for testing purposes: add in a blue bounding box to faces
                        cv2.rectangle(orig_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                        trackBox = dlib.rectangle(x, y, x + w, y + h)
                        tracker.start_track(grey, trackBox)
                        trackingFace = True
                else:
                    trackingFace = False
                    capture_frame = True

            # If we are tracking a face, update the tracker
            else:
                trackingQuality = tracker.update(grey)

                # If the tracking quality is below our threshold, stop track & resume capture
                if trackingQuality < 8.75:
                    trackingFace = False
                    capture_frame = True

                # If our tracker is good enough quality, keep track & pause capture
                else:
                    trackingFace = True
                    capture_frame = False

            if capture_frame:
                screenshots_count += 1

                print("Duration of screenshot %.3f (%.3f - %.3f)" % (helpers.get_duration_ms(fps, frame_count) - helpers.get_duration_ms(fps, last_scene_start), helpers.get_duration_ms(fps, last_scene_start), helpers.get_duration_ms(fps, frame_count)))
                # https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html#ggaeb8dd9c89c10a5c63c139bf7c4f5704daf01bc92359d2abc9e6eeb5cbe36d9af2
                print("Duration through clip %.3f" % cap.get(cv2.CAP_PROP_POS_MSEC))
                # Write out the filename including the frame range that covers
                png_filename = f"{screenshots_count:03}_{last_scene_start}-{frame_count}.png"
                last_scene_start = frame_count
                out_file_path = os.path.join(output_dir_path, png_filename)
                print(f"Saving file at: {out_file_path}")
                cv2.imwrite(out_file_path, orig_frame)
            

        # p_non_zero >= MIN_PERCENT_THRESH, indicates motion/animations.
        # Hence wait till the motion across subsequent frames has settled down.
        elif capture_frame and p_non_zero >= MIN_PERCENT_THRESH:
            capture_frame = False

        
        frame_count += 1

        # For testing exit after x ms
        #mins = 6
        #if float(cap.get(cv2.CAP_PROP_POS_MSEC)) > (mins * 60 * 1000.0):
        #    break


    end_time = time.time()
    print('***'*10,'\n')
    print("Statistics:")
    print('---'*10)
    print(f'Total Time taken: {round(end_time-start, 3)} secs')
    print(f'Total Screenshots captured: {screenshots_count}')
    print('---'*10,'\n')
    
    # Release Video Capture object.
    cap.release()



if __name__ == "__main__":
        
    parser = argparse.ArgumentParser(description="This script is used to convert video frames into slide PDFs.")
    parser.add_argument("-v", "--video_file_path", help="Path to the video file", type=str)
    parser.add_argument("-o", "--out_dir", default = 'output_results', help="Path to the output directory", type=str)
    parser.add_argument("--type", help = "type of background subtraction to be used", default = 'GMG', 
                        choices=['Frame_Diff', 'GMG', 'KNN'], type=str)
    parser.add_argument("--no_post_process", action="store_true", default=False, help="flag to apply post processing or not")
    parser.add_argument("--convert_to_pdf", action="store_true", default=False, help="flag to convert the entire image set to pdf or not")
    args = parser.parse_args()


    video_path = args.video_file_path
    output_dir_path = args.out_dir
    type_bg_sub = args.type


    output_dir_path = create_output_directory(video_path, output_dir_path, type_bg_sub)

    if type_bg_sub.lower() == 'frame_diff':
        capture_slides_frame_diff(video_path, output_dir_path)
    
    else:

        if type_bg_sub.lower() == 'gmg':
            thresh = DEC_THRESH
        elif type_bg_sub.lower() == 'knn':
            thresh = DIST_THRESH

        capture_slides_bg_modeling(video_path, output_dir_path, type_bgsub=type_bg_sub,
                                   history=FRAME_BUFFER_HISTORY, threshold=thresh,
                                   MIN_PERCENT_THRESH=MIN_PERCENT, MAX_PERCENT_THRESH=MAX_PERCENT)

    # Perform post-processing using difference hashing technique to remove duplicate slides.
    if not args.no_post_process:
        remove_duplicates(output_dir_path)


    if args.convert_to_pdf:
        convert_slides_to_pdf(video_path, output_dir_path)

    
    