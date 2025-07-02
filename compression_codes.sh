ffmpeg -i input.mp4 -c:v libx265 -bf 0 output_no_bframes.mp4
ffmpeg -i input.mp4 -c:v libx264 -intra output_all_i.mp4


ffmpeg -i input.mp4 -c:v libx264 -x264-params scenecut=0:keyint=999:rc-lookahead=0:ref=4:ltrefs=1 output_ltr.mp4
ffmpeg -i input.mp4 -c:v libx265 -x265-params keyint=999:min-keyint=999:scenecut=0:ref=4 output_ltr.mp4

#  H.265’s LTR control in x265 isn't exposed via a specific ltrefs option in FFmpeg CLI. You can enable it via the x265 API if you compile custom code or patch FFmpeg.

# In practice, H.265 may implicitly use long-term referencing based on rate-distortion optimization, especially when ref is large and keyint is high.

ffmpeg -i input.mp4 -c:v libx265 -x265-params "ref=4:keyint=60:bframes=0:scenecut=0" output.mp4

#Flag	Description
#ref=4	Allows up to 4 reference frames (enables LTR usage)
#keyint=60	Sets GOP size (you can tune this as needed)
#bframes=0	No B-frames (only I and P)
#scenecut=0	Prevent random I-frames that break LTR chains

# Note: libx265 auto-selects references from the available list. To force a long-term reference, you need to patch libx265 at the API level (see below).
#  Modify libx265 API Usage in FFmpeg

#Verifying the Effect
#Use ffprobe to inspect frame types and references:
# ffprobe -select_streams v -show_frames -show_entries frame=pict_type,pkt_pts_time -of csv output.mp4

