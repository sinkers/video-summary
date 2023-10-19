import scenedetect
import sys

video_file = 'files/allhands.m4f'
video = scenedetect.open_video(video_file)
#scene_list = scenedetect.detect(video_file, scenedetect.ContentDetector(), end_time="00:02:00")
print("Detecting using Content")
scene_manager = scenedetect.SceneManager()
scene_manager.add_detector(scenedetect.ContentDetector())
scene_manager.detect_scenes(video, end_time=50000)
scene_list = scene_manager.get_scene_list()

for i, scene in enumerate(scene_list):
    print('Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
        i+1,
        scene[0].get_timecode(), scene[0].get_frames(),
        scene[1].get_timecode(), scene[1].get_frames(),))
    
sys.exit()
    
#scene_manager.save_images(scene_list, video, num_images=3, frame_margin=1, image_extension='jpg', encoder_param=95, image_name_template='$VIDEO_NAME-Scene-$SCENE_NUMBER-$IMAGE_NUMBER', output_dir="files/scenedetect-content", show_progress=False, scale=None, height=None, width=None)
scenedetect.scene_manager.save_images(scene_list, video, output_dir="files/scenedetect-content")

#scene_list = scenedetect.detect(video, scenedetect.ThresholdDetector())
#print(scene_list)
#scenedetect.scene_manager.save_images(scene_list, video, num_images=3, frame_margin=1, image_extension='jpg', encoder_param=95, image_name_template='$VIDEO_NAME-Scene-$SCENE_NUMBER-$IMAGE_NUMBER', output_dir="files/scenedetect-threshold", show_progress=False, scale=None, height=None, width=None)

print("Detecting using Threshold")
video.seek(0)
scene_manager.clear()
scene_manager.clear_detectors()
scene_manager.add_detector(scenedetect.ThresholdDetector(threshold=15))
scene_manager.detect_scenes(video)
scene_list = scene_manager.get_scene_list()

for i, scene in enumerate(scene_list):
    print('Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
        i+1,
        scene[0].get_timecode(), scene[0].get_frames(),
        scene[1].get_timecode(), scene[1].get_frames(),))
    
#scene_manager.save_images(scene_list, video, num_images=3, frame_margin=1, image_extension='jpg', encoder_param=95, image_name_template='$VIDEO_NAME-Scene-$SCENE_NUMBER-$IMAGE_NUMBER', output_dir="files/scenedetect-content", show_progress=False, scale=None, height=None, width=None)
scenedetect.scene_manager.save_images(scene_list, video, output_dir="files/scenedetect-threshold")

#scene_list = scenedetect.detect(video, scenedetect.AdaptiveDetector())
#print(scene_list)
#scenedetect.scene_manager.save_images(scene_list, video, num_images=3, frame_margin=1, image_extension='jpg', encoder_param=95, image_name_template='$VIDEO_NAME-Scene-$SCENE_NUMBER-$IMAGE_NUMBER', output_dir="files/scenedetect-adaptive", show_progress=False, scale=None, height=None, width=None)

print("Detecting using AdaptiveDetector")
video.seek(0)
scene_manager.clear()
scene_manager.clear_detectors()
scene_manager.add_detector(scenedetect.AdaptiveDetector())
scene_manager.detect_scenes(video)
scene_list = scene_manager.get_scene_list()

for i, scene in enumerate(scene_list):
    print('Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
        i+1,
        scene[0].get_timecode(), scene[0].get_frames(),
        scene[1].get_timecode(), scene[1].get_frames(),))
    
#scene_manager.save_images(scene_list, video, num_images=3, frame_margin=1, image_extension='jpg', encoder_param=95, image_name_template='$VIDEO_NAME-Scene-$SCENE_NUMBER-$IMAGE_NUMBER', output_dir="files/scenedetect-content", show_progress=False, scale=None, height=None, width=None)
scenedetect.scene_manager.save_images(scene_list, video, output_dir="files/scenedetect-adaptive")