# Physical Load Assessment
Physical Load Assessment methodologies used for the study titled "Towards automated ergonomic assessment using wearable sensors and surveys" by Thiery, E. et al.

[![DOI](https://zenodo.org/badge/996659273.svg)](https://doi.org/10.5281/zenodo.15674544)

## 1. Requirements:

### Hardware:
- Movella Xsens Awinda
- Moticon Insoles OR Project Aria smart glasses
- Windows 10/11 system x64/x86
- second system running x64 Ubuntu jammy (22.04) or newer (only if using smart glasses)
- Android smartphone with Moticon OpenGo app OR Project Aria companion app

### Software:
- Visual Studio 2019 or above
- Visual Studio Code or Similar IDE to run/debug python scripts
- MVN Analyze Pro 2024 ([Tutorials](https://www.movella.com/tutorials))
- Moticon OpenGo desktop app ([Customer access](https://account.moticon.com/login))
- DataManager LSL app ([GitHub Link](https://github.com/ielmakri/PhysioSense/tree/main/apps/DataManager))
- Xsens Client LSL app ([GitHub Link](https://github.com/ielmakri/PhysioSense/tree/main/apps/XsensClient))
- Moticon Client LSL app ([GitHub Link](https://github.com/ielmakri/PhysioSense/tree/main/apps/MoticonClient)) (if using insoles)
- Project Aria Client SDK ([Tutorials](https://facebookresearch.github.io/projectaria_tools/docs/ARK/sdk/setup)) (if using smart glasses)
- Physical load Python apps ([GitHub Link](https://github.com/EliasThiery/physical_load_assessment_Thiery_et_al/code/)) (this Github)
- Python 3.9 or above
- .NET 5.0 or higher

## 2. Description:
Automation of the EAWS score calculations for postural and carried load analysis using CSV files generated from Xsens IMU and Project Aria smart glasses (or Moticon insoles) data streams. The software is built up using the LSL clients developed within the AugmentX infrastructure such as “Xsens LSL app”, "Moticon LSL app" and “DataManager App”. The physical load assessment tool also allows overlaying EAWS scores and recognized postures and loads onto an existing recorded video of the user motions.

## 3. Action to Start Physical Load Assessment:

1. Launch MVN Analyze Pro 2024 and follow the steps to add a model and calibration ([Tutorial Link](https://www.movella.com/tutorials)).
2. In options > Network streamer, make sure that "joint angles", "euler angles" and "quaternions" are enabled.
3. If using Project Aria smart glasses: follow steps 4-5, if using Moticon insoles: follow steps 6-8.
4. Launch Project Aria Companion app and connect to the same Wi-Fi network as the Linux system. Make sure this network has no restrictions, as university networks may block communication. Note the IP-address of the glasses.
5. Start the marker_detection.py script on the Linux system using the glasses IP-address:

`python -m marker_detection --interface wifi --update_iptables --device-ip <Glasses IP>`

6. Launch Moticon OpenGo (both the smartphone and desktop apps).
7. Making sure that both devices are on the same network, change the port number and IP address in the settings of the smartphone app (Record > bottom left cog icon) to the ones shown in the desktop app (Record > top right cog icon > Controller). Make sure that the switches in "Controller" and "UDP output" are both set to on. Click "Check connection" in the smartphone app to verify if the connection is established. Also set the record mode in the smartphone app settings to "Live capture".
8. Perform the insole calibration (bottom right dial icon) and start recording (big red button).
 
 <p align="center">
   <img src="/resources/moticon_opengo.jpg" alt="">
 </p>
 
9. Open DataManager and prepare a recording session (record tab) and click “confirm”, return then to the “Main” tab.

 <p align="center">
   <img src="/resources/step5.jpg" alt="">
 </p>
 
10. Launch the Xsens LSL client app and click on “Start”.

 <p align="center">
   <img src="/resources/step6.jpg" alt="">
 </p>

11. Launch the Moticon LSL client app and click on “Start” (if using insoles).

 <p align="center">
   <img src="/resources/moticonclient.png" alt="">
 </p>
 
12. Go to the Main tab of DataManager and click “List”. You should see a list of xsens streamers and the marker stream (if using smart glasses) or insole stream (if using insoles).

 <p align="center">
   <img src="/resources/step9.jpg" alt="">
 </p>
 
13. Click on “Check all” > “Subscribe” > “Record”, the recording starts and the “record” button toggles to “stop”.

  <p align="center">
   <img src="/resources/step10.jpg" alt="">
 </p>

14. Start the camera recording (only necessary if you want to generate the video rendering with EAWS score overlay).
15. Stop the recording when desired.
16. Open 'har_rt_carried_loads.py' and change the operator and base file names to the appropriate ones (saved in the folder specified by DataManager). Also choose the load_type variable: either 'glasses' or 'insoles'. Fill in the base filename and path variables based on the names of the raw csv data files. You may have to change some of the hard-coded parts of the file name, depending on the name of the files output by the Data Manager. Then run the program.

```
#define file names

load_type = "glasses"    #type of load source to use, either "glasses" or "insoles"
operator = Operator("John Doe","M",185,60)
base_filename = "sess1_JohnD"
path = "C:\\Users\\ethiery\\Documents\\Wellficiency\\PhysicalLoad\\physical_load_paper_experiments\\proovit\\sess1\\JohnD\\"
ergo_csv = path + base_filename + "_Xsens-Awinda (AugmentXVR)_hum_ergo_feat.csv"
if load_type == "insoles":
    load_csv = [path + base_filename + "_Moticon-Insole3 (DICT-5CG20936LR)_l_f.csv", path + base_filename + "_Moticon-Insole3 (DICT-5CG20936LR)_r_f.csv"]
elif load_type == "glasses":
    load_csv = path + base_filename + "_DetectedMarkers (elias-HP-EliteBook-850-G8-Notebook-PC)_marker_id.csv"
pos_csv = path + base_filename + "_Xsens-Awinda (AugmentXVR)_hum_pos.csv"
```

17. Two csv files (ending in AutoDeLoad and AutoDePos) will be generated containing the recognised postures and load events throughout the session. These are placed in the current folder for the next steps (calculating EAWS/KIM).
18. Move the recorded video (if it was made) to the folder with `physical_load.py`. Set the operation variable to either "video" or "files", depending on if you want to overlay the scores on the recorderded video or simply write them to csv files. Run `physical_load.py`.

 ```
operator1 = Operator("John Doe", "M", 185, 65)
task = Task('Task 1')
operation = "video"
physical_load = PhysicalLoad("EAWS", "sess1_JohnD - AutoDePos.csv", "sess1_JohnD - AutoDeLoad.csv", operator1, task)
print("Score:", physical_load.calculate_score())
print("baseline survey score: ", physical_load.calculate_baseline_score("Wellficiency_baseline_survey.csv"))
print("NASA TLX score: ", physical_load.calculate_TLX_score("Wellficiency_NASA_TLX.csv"))
if operation == "video":
    physical_load.process_video_with_posture("sess1_JohnD.mp4", "output_sess1_JohnD.mp4")
elif operation == "files"
    physical_load.save_physical_scores_to_file()
```
 
20. A video will be generated (“output.mp4” or similar) with the EAWS/KIM scores and recognized postures and loads if the 'video' option was chosen. You can also simply save the score evolution over time to a csv file using the 'save_physical_scores_to_file' function.

