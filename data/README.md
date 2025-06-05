This readme file was generated on 2025-05-23 by Elias Thiery

# GENERAL INFORMATION

* Title of Dataset: WellFiciency physical load proovit-palletizing experiments

## Author/Principal Investigator Information
Name: Elias Thiery
ORCID: 0009-0006-2697-4382
Institution: Vrije Universiteit Brussel
Address: Pleinlaan 2, 1050 Brussels
Email: elias.thiery@vub.be

## Author/Associate or Co-investigator Information
Name: Ilias El Makrini
ORCID: 0000-0002-9980-517X
Institution: Vrije Universiteit Brussel
Address: Pleinlaan 2, 1050 Brussels
Email: ilias.el.makrini@vub.be

* Date of data collection: 2025-04-23 until 2025-05-07
* Geographic location of data collection: AugmentX laboratory, Vrije Universiteit Brussel, Brussels, Belgium
* Information about funding sources that supported the collection of the data: The study for which this data was collected was supported by a grant of the Research Foundation - Flanders (FWO SBO WellFiciency)


# SHARING/ACCESS INFORMATION

* Licenses/restrictions placed on the data: Attribution License (ODC-By): Users are free to use the database and its content in new and different ways, provided they provide attribution to the source of the data and/or the database.

* Recommended citation for this dataset: Thiery, E., Incirci, T., Martens, J., Bal, M., Dessers, E., Verstraten, T. & El Makrini, I. (2025). WellFiciency physical load proovit-palletizing experiments [data file]. Brussels, Belgium: Robotics & Multibody Mechanics research group, Vrije Universiteit Brussel [producer]. Brussels, Belgium: Robotics & Multibody Mechanics research group, Vrije Universiteit Brussel [distributor].


# DATA & FILE OVERVIEW

## File List:
palletizing: folder containing data from the palletizing experiment
	∟sess1: folder containing data from the first and only session
		∟partX: folder containing data from participant X
			sess1_partX - AutoDeLoad_palletizing.csv: file containing all load events detected during the experiment
			sess1_partX - AutoDePos_palletizing.csv: file containing all postures detected during the experiment
			sess1_partX_DetectedMarkers (HP-EliteBook-850-G8-Notebook-PC)_marker_id.csv: file containing all markers 					detected by the smart glasses during the experiment
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_ergo_feat: file containing raw joint angle and position data from IMUs 				related to ergonomic features (used to determine posture)
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_joint_ang: file containing all raw joint angle data from IMUs
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_pos: file containing all body segment position data from IMUs		
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_rot: file containing all body segment orientation data from IMUs
			*FILE_NAME*.json: metadata for each data stream

proovit: folder containing data from the ProoVit assembly experiment
	∟sess1: folder containing data from the first and only session
		∟partX: folder containing data from participant X
			sess1_partX - AutoDeLoad_proovit.csv: file containing all load events detected during the experiment
			sess1_partX - AutoDePos_proovit.csv: file containing all postures detected during the experiment
			sess1_partX_DetectedMarkers (HP-EliteBook-850-G8-Notebook-PC)_marker_id.csv: file containing all markers 					detected by the smart glasses during the experiment
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_ergo_feat: file containing raw joint angle and position data from IMUs 				related to ergonomic features (used to determine posture)
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_joint_ang: file containing all raw joint angle data from IMUs
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_pos: file containing all body segment position data from IMUs		
			sess1_partX_Xsens-Awinda (AugmentXVR)_hum_rot: file containing all body segment orientation data from IMUs
			*FILE_NAME*.json: metadata for each data stream

physical_load_data_analysis_pseudonomyzed.csv: csv file containing all resulting data from the automatic and manual EAWS calculations, as well as subjective data. Note that the data from part9 for the palletizing experiment was excluded because of a malfunction of the IMUs.

Wellficiency_baseline_survey.csv: csv file containing the results of the baseline survey for all participants. Only questions 3.1.2, 3.4.1, 3.4.2, 3.4.4, 3.6.2 and 3.10.1 up to and including 3.10.11 are relevant to the physical load and thus the rest are left blank.

Wellficiency_NASA_TLX.csv: csv file containing the results of the NASA TLX survey for all participants, for both experiments.

README.txt: this README file		

* Relationship between files: The participant name is consistent throughout all files, i.e. partX in proovit is the same participant as partX in palletizing

This is the only version of the dataset.


# METHODOLOGICAL INFORMATION

## Description of methods used for collection/generation of data:
The data was collected using the methods described in the following paper:

Thiery, E., Incirci, T., Martens, J., Bal, M., Dessers, E., Verstraten, T. & El Makrini, I. (2025). Towards automated ergonomic assessment using wearable sensors and surveys.

## Methods for processing the data:
The raw IMU and smart glasses data was processed using the Python scripts described in the above publication (INSERT GITHUB LINK HERE).

## Instrument- or software-specific information needed to interpret the data:
raw data collected using Xsens Awinda IMUs and Xsens MVN 2024.0, and Project Aria smart glasses and Aria companion app.
data processed using physical load Python scripts (INSERT GITHUB LINK HERE). These require the following Python packages: sys, datetime, bisect, math, json, os, pandas, numpy, matplotlib, collections, pylsl, scipy, warnings, cv2, copy, requests, pytz


The EAWS scores were calculated according to the EAWS procedure described in the following paper:

Schaub, K., Caragnano, G., Britzke, B., & Bruder, R. (2012). The European Assembly Worksheet. Theoretical Issues in Ergonomics Science, 14(6), 616–639. https://doi.org/10.1080/1463922X.2012.678283


# DATA-SPECIFIC INFORMATION FOR: sess1_partX - AutoDeLoad_EXPERIMENT_NAME.csv

* Number of variables: 9
* Number of cases/rows: depends on the participant
* Variable List: type (type of load event),transport (transportation vehicle, None if no vehicle is used),weight (kg),posture (points awarded to the load event depending on the posture as described in the EAWS method),conditions (working conditions, always 0 because they cannot be detected by sensors),frequency (#/shift) (frequency of repositionings),duration (min/shift) (duration of holdings),distance (m/shift) (distance traveled during carrying),time (HH:mm:ss.fff)


# DATA-SPECIFIC INFORMATION FOR: sess1_partX - AutoDePos_EXPERIMENT_NAME.csv

* Number of variables: 2
* Number of cases/rows: depends on the participant
* Variable List: Time[HH:mm:ss.fff],Pose (string encoding the posture type, containing global posture type, specific posture type, far reach index, trunk rotation index and lateral bending index, see the associated publication for a more detailed explanation)


# DATA-SPECIFIC INFORMATION FOR: sess1_partX_DetectedMarkers (HP-EliteBook-850-G8-Notebook-PC)_marker_id.csv

* Number of variables: 2
* Number of cases/rows: depends on the participant
* Variable List: Time[HH:mm:ss.fff],Ch1[] (ID of the currently detected marker)


# DATA-SPECIFIC INFORMATION FOR: sess1_partX_Xsens-Awinda (AugmentXVR)_hum_ergo_feat.csv

* Number of variables: 10
* Number of cases/rows: depends on the participant
* Variable List: Time[HH:mm:ss.fff], JOINT_OR_SEGMENT_NAME_x[deg/m], JOINT_OR_SEGMENT_NAME_y[deg/m], JOINT_OR_SEGMENT_NAME_z[deg/m] (x,y,z angles or positions of joint or body segment)


# DATA-SPECIFIC INFORMATION FOR: sess1_partX_Xsens-Awinda (AugmentXVR)_hum_joint_ang.csv

* Number of variables: 84
* Number of cases/rows: depends on the participant
* Variable List: Time[HH:mm:ss.fff], JOINT_NAME_x[deg], JOINT_NAME_y[deg], JOINT_NAME_z[deg] (x,y,z angles of joint)
* NOTE: THE JOINT NAMES ARE NOT ALL ACCURATE. PLOT THEIR VALUES IN A 3D PLOT TO CHECK WHETHER THEY ARE CORRECTLY ASSOCIATED.


# DATA-SPECIFIC INFORMATION FOR: sess1_partX_Xsens-Awinda (AugmentXVR)_hum_pos.csv

* Number of variables: 69
* Number of cases/rows: depends on the participant
* Variable List: Time[HH:mm:ss.fff], BODY_SEGMENT_NAME_x[m], BODY_SEGMENT_NAME_y[m], BODY_SEGMENT_NAME_z[m] (x,y,z positions of body segment)
* NOTE: THE SEGMENT NAMES ARE NOT ALL ACCURATE. PLOT THEIR VALUES IN A 3D PLOT TO CHECK WHETHER THEY ARE CORRECTLY ASSOCIATED.


# DATA-SPECIFIC INFORMATION FOR: sess1_partX_Xsens-Awinda (AugmentXVR)_hum_rot.csv

* Number of variables: 69
* Number of cases/rows: depends on the participant
* Variable List: Time[HH:mm:ss.fff], BODY_SEGMENT_NAME_x[deg], BODY_SEGMENT_NAME_y[deg], BODY_SEGMENT_NAME_z[deg] (x,y,z orientation of body segment)
* NOTE: THE SEGMENT NAMES ARE NOT ALL ACCURATE. PLOT THEIR VALUES IN A 3D PLOT TO CHECK WHETHER THEY ARE CORRECTLY ASSOCIATED.
