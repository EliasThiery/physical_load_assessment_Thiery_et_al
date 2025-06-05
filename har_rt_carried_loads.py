# Python ≥3.11 is required
import sys
import datetime
import bisect
import math
import json
import os

assert sys.version_info >= (3, 11)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from pylsl import StreamInlet, StreamOutlet, StreamInfo, resolve_stream
from scipy.signal import butter, lfilter, freqz
from participant import Operator

import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")

position_Pelvis_z = "Pelvis z.1"
jRight_Hip_x = "Pelvis_T8 Axial Bending"     #trunk rotation
jRight_Hip_y = "Pelvis_T8 Lateral Bending"   #trunk lateral bending
Vertical_T8_z = "Pelvis_T8 Flexion/Extension" #trunk forward bending
jLeftShoulder_y = "Left Shoulder Abduction/Adduction"
jLeftShoulder_z = "Left Shoulder Flexion/Extension"
jRightShoulder_y = "Right Shoulder Abduction/Adduction"
jRightShoulder_z = "Right Shoulder Flexion/Extension"
jLeftElbow_z = "Left Elbow Flexion/Extension"
jRightElbow_z = "Right Elbow Flexion/Extension"


EAWS_Standing = "St"
EAWS_Crouching = "Cr"
EAWS_Lying = "Ly"
EAWS_Upright = "U"
EAWS_BentForward = "BF"
EAWS_BentStrongForward = "BS"
EAWS_ElbowOverShoulder = "OS"
EAWS_HandsAboveHead = "OH"
EAWS_FarReach = "FR"
EAWS_TrunkRotation = "TR"
EAWS_LateralBending = "LB"


def auto_label(df):
    # Constants
    MULT_PELVIS_Z_LY = 0.2
    MULT_PELVIS_Z_CR = 0.85
    TH_PELVIS_BF = 20
    TH_PELVIS_BS = 60
    TH_PELVIS_BS_NEG = -100
    TH_SHOULDER_OS = 75
    TH_SHOULDER_OH = 110
    TH_SHOULDER_FR = 50
    OFFSET_CR = 0
    OFFSET_SHOULDER_BF_Y = 0  # Dynamic using -> df[jRight_Hip_y]
    OFFSET_SHOULDER_BF_Z = 0  # Dynamic using -> df[Vertical_T8_z]

    st_u_L5_avg = 1.0 #df[position_Pelvis_z][:8].mean(skipna=True) --> TO CHECK

    # Main poses: St, Ly, Cr
    df["AutoDePos"] = "St"  # Default value
    # Use vectorized updates for main poses
    df["AutoDePos"] = np.where(df[position_Pelvis_z] < MULT_PELVIS_Z_LY * st_u_L5_avg, "Ly", "St")
    df["AutoDePos"] = np.where(
        (df[position_Pelvis_z] >= MULT_PELVIS_Z_LY * st_u_L5_avg) & (df[position_Pelvis_z] < MULT_PELVIS_Z_CR * st_u_L5_avg), "Cr", df["AutoDePos"]
    )
    df["AutoDePos"] = np.where(
        (df["AutoDePos"] == "Ly") & (df[Vertical_T8_z] < TH_PELVIS_BF), "Cr", df["AutoDePos"]
    )

    #print(st_u_L5_avg)
    # print(df[position_Pelvis_z], " ", MULT_PELVIS_Z_LY * st_u_L5_avg, " : ", MULT_PELVIS_Z_CR * st_u_L5_avg)
    # condition_cr = ((df[jLeftHip_z] > 30) |  (df[jLeftKnee_z] > 30) ) & ((df[jRightHip_z] > 30) |  (df[jRightKnee_z] > 30) )

    #df.loc[
    #    condition_cr,
    #    "AutoDePos",
    #] = "Cr"

    """(
            (df[jLeftShoulder_y] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Y)
            | (df[jLeftShoulder_z] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Z)
            | (df[jRightShoulder_y] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Y)
            | (df[jRightShoulder_z] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Z)
        ),
        (
            (df[jLeftShoulder_y] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Y)
            | (df[jLeftShoulder_z] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Z)
            | (df[jRightShoulder_y] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Y)
            | (df[jRightShoulder_z] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Z)
        ),"""
    
    # Symmetric sub-poses: : BF, BS, OH, OS, U
    conditions_sym = [
        (((df[Vertical_T8_z] >= TH_PELVIS_BS ) | (df[Vertical_T8_z] <= TH_PELVIS_BS_NEG)) & (df["AutoDePos"] == "St")),
        (((df[Vertical_T8_z] >= TH_PELVIS_BS + OFFSET_CR) | (df[Vertical_T8_z] <= TH_PELVIS_BS_NEG + OFFSET_CR)) & (df["AutoDePos"] == "Cr")),
        ((df[Vertical_T8_z] >= TH_PELVIS_BF) & (df["AutoDePos"] == "St")),
        ((df[Vertical_T8_z] >= TH_PELVIS_BF + OFFSET_CR) & (df["AutoDePos"] == "Cr")),
        (
            (df[jLeftShoulder_z] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Z)
            | (df[jRightShoulder_z] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Z)
        ),
        (
            (df[jLeftShoulder_z] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Z)
            | (df[jRightShoulder_z] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Z)
        ),
        ((df[Vertical_T8_z] < TH_PELVIS_BF) & (df["AutoDePos"] != "Cr")),
        ((df[Vertical_T8_z] < TH_PELVIS_BF + OFFSET_CR) & (df["AutoDePos"] == "Cr")),
    ]
    choices_sym = ["_BS", "_BS", "_BF", "_BF", "_OH", "_OS", "_U", "_U"]

    # Define precedence for choices_sym
    precedence_order = {"_BS": 1, "_BF": 2, "_OH": 3, "_OS": 4, "_U": 5}

    # Initialize a column to store the choice with the highest precedence
    df["Sym_Label"] = ""

    for condition, choice in zip(conditions_sym, choices_sym):
        # Replace with precedence order and fill missing values
        precedence_values = df["Sym_Label"].map(precedence_order).fillna(float("inf"))

        # Only update if the current condition is met and the new choice has higher precedence
        df["Sym_Label"] = np.where(
            condition & (precedence_values > precedence_order.get(choice, float("inf"))),
            choice,
            df["Sym_Label"]
        )

    # Append the highest-priority label to `AutoDePos`
    df["AutoDePos"] = np.where(
        df["Sym_Label"] != "",
        df["AutoDePos"].str.replace("|".join(precedence_order.keys()), "") + df["Sym_Label"],
        df["AutoDePos"]
    )

    # Drop intermediate column
    df.drop(columns=["Sym_Label"], inplace=True)

    label_fr = True
    if label_fr:
        # Asymmetric sub-poses: Far reach
        thresholds_fr = np.array([5, 20, 35, 50, 70, 180])
        choices_fr = ["_FR5", "_FR4", "_FR3", "_FR2", "_FR1", "_FR0"]

        # Use np.select to apply conditions in one step
        df["Fr_Labels"] = np.select(
            [((df[jLeftElbow_z] < t) & (df[jLeftShoulder_z] >= TH_SHOULDER_FR)) | ((df[jRightElbow_z] < t) & (df[jRightShoulder_z] >= TH_SHOULDER_FR)) for t in thresholds_fr], choices_fr, default="_FR0"
        )

        # Avoid overwriting existing labels in `AutoDePos` if already contains a far reach label
        df["AutoDePos"] = np.where(
            df["AutoDePos"].str.contains("|".join(choices_fr)),
            df["AutoDePos"],
            df["AutoDePos"] + df["Fr_Labels"],
        )

        # Drop intermediate column used for labeling
        df.drop(columns=["Fr_Labels"], inplace=True)
    else:
        #set all labels to FR0
        df["Fr_Labels"] = np.select(
            abs(df[jLeftShoulder_y]) >= 0, ["_FR0"], default=""
        )

        df["AutoDePos"] = df["AutoDePos"] + df["Fr_Labels"]

        # Drop intermediate column used for labeling
        df.drop(columns=["Fr_Labels"], inplace=True)

    # Asymmetric sub-poses: Trunk rotations
    thresholds_tr = np.array([30, 25, 20, 15, 10, 0])
    choices_tr = ["_TR5", "_TR4", "_TR3", "_TR2", "_TR1", "_TR0"]

    # Use np.select to apply conditions in one step
    df["Tr_Labels"] = np.select(
        [abs(df[jRight_Hip_y]) > t for t in thresholds_tr], choices_tr, default=""
    )

    # Avoid overwriting existing labels in `AutoDePos` if already contains a trunk label
    df["AutoDePos"] = np.where(
        df["AutoDePos"].str.contains("|".join(choices_tr)),
        df["AutoDePos"],
        df["AutoDePos"] + df["Tr_Labels"],
    )

    # Drop intermediate column used for labeling
    df.drop(columns=["Tr_Labels"], inplace=True)

    # Asymmetric sub-poses: Trunk lateral bendings
    # Calculate thresholds for trunk lateral bending
    thresholds_lb = np.array([30, 25, 20, 15, 10, 0])
    choices_lb = ["_LB5", "_LB4", "_LB3", "_LB2", "_LB1", "_LB0"]

    # Use np.select to apply conditions in one step
    df["Lb_Labels"] = np.select(
        [abs(df[jRight_Hip_x]) > t for t in thresholds_lb], choices_lb, default=""
    )

    # Avoid overwriting existing labels in `AutoDePos` if already contains a lateral bending label
    df["AutoDePos"] = np.where(
        df["AutoDePos"].str.contains("|".join(choices_lb)),
        df["AutoDePos"],
        df["AutoDePos"] + df["Lb_Labels"],
    )

    # Drop intermediate column used for labeling
    df.drop(columns=["Lb_Labels"], inplace=True)

    return df

def split_into_sublists(data, range_limit):
    if not data:
        return []

    sublists = []
    current_avg = data[0][1]  # Initialize the current average with the first element's value
    current_sublist = [data[0]]             # Start the first sublist with the first element

    for i, load in enumerate(data[1:]):
        if abs(load[1] - current_avg) <= range_limit:
            current_sublist.append(load)
        else:
            sublists.append(current_sublist)
            current_avg = np.mean([load[1] for load in data[i+1:i+10]])
            current_sublist = [load]  # Start a new sublist with the current number

    # Append the last sublist
    sublists.append(current_sublist)

    return sublists

def most_frequent(List):
    if not List:
        return None
    counter = 0
    most = List[0]
     
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency > counter):
            counter = curr_frequency
            most = i
 
    return most

def parse_time(time_str):
    time_format = "%H:%M:%S.%f"
    try:
        parsed_time = datetime.datetime.strptime(time_str, time_format)
        total_seconds = parsed_time.hour * 3600 + parsed_time.minute * 60 + parsed_time.second + parsed_time.microsecond / 1e6
        return total_seconds
    except ValueError:
        return None
    
def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def find_distance_carried(carrying_event, pos_data):
    #calculates total distance travelled for specific carrying event
    distance = 0
    pos_data_timestamps = [i[0] for i in pos_data]
    pos_index = 0
    pos_index = bisect.bisect_left(pos_data_timestamps,carrying_event[0][0],pos_index)    #finds index of pos_data to insert load timestamp into so that it stays sorted, i.e. index of element with timestamp closest to that of load
    if pos_index >= len(pos_data):
            pos_index -= 1
    previous_pos = [[pos_data[pos_index][46], pos_data[pos_index][47]],[pos_data[pos_index][58], pos_data[pos_index][59]]]
    for load in carrying_event[:-1]:
        pos_index = bisect.bisect_left(pos_data_timestamps,load[0],pos_index)    #finds index of pos_data to insert load timestamp into so that it stays sorted, i.e. index of element with timestamp closest to that of load
        if pos_index >= len(pos_data):
            pos_index -= 1
        current_pos = [[pos_data[pos_index][46], pos_data[pos_index][47]],[pos_data[pos_index][58], pos_data[pos_index][59]]]
        distance += max([math.sqrt(sum([(current_pos[k][j] - previous_pos[k][j])**2 for j in range(2)])) for k in range(2)])        #calculate how much legs has moved since last sample
        previous_pos = current_pos
    return distance

def main():
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

    #start = int(datetime.datetime.now().timestamp())
    #print("start")

    #label posture data
    label_posture = False

    if label_posture:
        #without elbow angles
        """columns_list = [
                position_Pelvis_z,
                Pelvis_T8_x,
                Pelvis_T8_y,
                Pelvis_T8_z,
                jLeftShoulder_y,
                jLeftShoulder_z,
                jRightShoulder_y,
                jRightShoulder_z,
            ]"""
        #with elbow angles
        columns_list = [
                position_Pelvis_z,
                jRight_Hip_x,
                jRight_Hip_y,
                Vertical_T8_z,
                jLeftShoulder_y,
                jLeftShoulder_z,
                jRightShoulder_y,
                jRightShoulder_z,
                jLeftElbow_z,
                jRightElbow_z,
            ]
        
        # Read the data in bulk (skip unnecessary lines upfront)
        df_raw = pd.read_csv(ergo_csv, skiprows=8, header=None, names=["timestamp"] + columns_list)  # Adjust `columns_list` as needed
        df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"])  # Convert timestamps to datetime

        # Efficient chunking (if memory is an issue)
        chunk_size = 20  # Process 20 rows at a time
        window_size_s = 0.25  # 250 ms in seconds

        #preallocate list to improve memory usage
        output = [""] * (len(df_raw) // chunk_size + 1)
        output_index = 0

        for start_idx in range(0, len(df_raw), chunk_size):
            chunk = df_raw.iloc[start_idx:start_idx + chunk_size].copy()
        
            # Calculate the rolling window statistics only for the last `window_size_s` window
            chunk["time_diff"] = (chunk["timestamp"] - chunk["timestamp"].iloc[-1]).dt.total_seconds().abs()
            filtered_chunk = chunk[chunk["time_diff"] <= window_size_s]
            
            samples_mean = filtered_chunk[columns_list].mean()

            # Prepare the labelled dataframe and apply `auto_label`
            labelled_chunk = pd.DataFrame([samples_mean], columns=columns_list)
            labelled_chunk["timestamp"] = chunk["timestamp"].iloc[-1]
            df_labelled = auto_label(labelled_chunk)

            # Extract plain values and format the output correctly
            timestamp_str = labelled_chunk["timestamp"].iloc[0].strftime("%H:%M:%S.%f")[:-3]  # Keep only milliseconds
            label_str = df_labelled["AutoDePos"].iloc[-1]  # Extract label
            output[output_index] = f"{timestamp_str},{label_str}"

            output_index += 1

        for i in range(chunk_size):
            if output[-i-1] == "":
                output.pop(-i-1)
        
        #get header
        with open(ergo_csv, "r") as file:
            lines = file.readlines()
            header = lines[:7]
        
        type = "AutoDePos"
        name = base_filename + " - " + type

        #write posture data to file
        with open(name + ".csv", "w") as file:
            for row in header:
                file.write(row)
            file.write("Time[HH:mm:ss.fff],Pose\n")
            for row in output:
                file.write(row)
                file.write("\n")    
        

        #print("stop: ", int(datetime.datetime.now().timestamp())-start)

        #create list of posture data
        posture_data = []
        start_time = parse_time(header[4].split(": ")[1].split()[1])
        for i in range(8,len(output)):
            time_str = output[i].split(",")[0]
            if "." not in time_str:
                time_str += ".0"
            posture_data.append([parse_time(time_str)-start_time, output[i].split(",")[1]])
    else:
        type = "AutoDePos"
        name = base_filename + " - " + type

        with open(name + ".csv", "r") as file:
            lines = file.readlines()
            header = lines[:7]

            start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1][0:-1]
            start_time = parse_time(start_time_line)

            #read posture data from csv file
            posture_data = []
            for line in lines[8:]:
                parts = line.strip().split(",")
                time_str = parts[0]
                if "." not in time_str:
                    time_str += ".0"
            posture_data.append([parse_time(time_str)-start_time, parts[1]])
        

    if load_type == "insoles":
        #load load data
        load_data = []

        #loop over all load csv files
        for filename_load in load_csv:
            with open(filename_load, "r") as file:
                lines = file.readlines()
                header = lines[:7]

                start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1][0:-1]
                start_time_load = parse_time(start_time_line)

                #read load data for each csv file
                load_data_component = []
                for line in lines[8:]:
                    parts = line.strip().split(",")
                    time_str = parts[0]
                    if "." not in time_str:
                        time_str += ".0"
                    load = float(parts[1])/(9.81*100)                    #convert N to kg, force values are multiplied by 100 for some reason
                    time_seconds = parse_time(time_str)
                    load_data_component.append([time_seconds-start_time_load, load])
                load_data.append(load_data_component)

        #combine load data and subtract starting value (assume subject not holding any load, so equal to body weight)
        initial_load = np.mean([sum([load_data[i][j][1] for i in range(len(load_data))]) for j in range(10,50)])
        print(f"initial load: {initial_load} kg")

        data = [[load[1] for load in load_data[0]], [load[1] for load in load_data[1]]]
        cutoff = 1.8      #cutoff freq in Hz
        #cutoff = 20
        fs = 50          #sample rate in Hz
        order = 1

        y = [butter_lowpass_filter(data[0], cutoff, fs, order), butter_lowpass_filter(data[1], cutoff, fs, order)]

        t = [[load[0] for load in load_data[0]], [load[0] for load in load_data[1]]]

        plt.plot(t[0], data[0], 'b-', label='data')
        plt.plot(t[0], y[0], 'g-', linewidth=2, label='filtered data')
        plt.ylabel('Load (kg)')
        plt.xlabel('Time [sec]')
        plt.title('Filtered load left foot')
        plt.grid()
        plt.legend()

        plt.subplots_adjust(hspace=0.35)
        plt.show()

        plt.plot(t[1], data[1], 'b-', label='data')
        plt.plot(t[1], y[1], 'g-', linewidth=2, label='filtered data')
        plt.ylabel('Load (kg)')
        plt.xlabel('Time [sec]')
        plt.title('Filtered load right foot')
        plt.grid()
        plt.legend()

        plt.subplots_adjust(hspace=0.35)
        plt.show()

        load_data = [[[t[0][i], y[0][i]] for i in range(len(y[0]))], [[t[1][i], y[1][i]] for i in range(len(y[1]))]]

        #sum load components
        load_data_summed = []
        max_length = max(len(component) for component in load_data)
        for i in range(max_length):
            total_load = 0
            time_set = False
            
            for component in load_data:
                if i < len(component):
                    if not time_set:
                        time_set = True
                        load_data_summed.append(component[i])            #copy first valid load component
                    total_load += component[i][1]
            
            if time_set:
                load_data_summed[-1][1] = total_load - initial_load          #update weight value to sum of components and subtract initial weight to get carried weight

        # Filter the data, and plot both the original and filtered signals.
        data = [load[1] for load in load_data_summed]
        cutoff = 0.2      #cutoff freq in Hz
        #cutoff = 10
        fs = 50          #sample rate in Hz
        order = 2

        y = butter_lowpass_filter(data, cutoff, fs, order)

        """window_size = 50
        numbers_series = pd.Series(data)
        
        # Create a series of moving averages of each window
        windows = numbers_series.rolling(window_size)
        moving_averages = windows.mean()
        moving_averages_list = moving_averages.tolist()
        
        # Remove null entries from the list
        y = moving_averages_list[window_size - 1:]"""

        #t = [load[0] for load in load_data_summed[window_size - 1:]]
        t = [load[0] for load in load_data_summed]

        #plt.plot(t, data[window_size - 1:], 'b-', label='data')
        plt.plot(t, data, 'b-', label='data')
        plt.plot(t, y, 'g-', linewidth=2, label='filtered data')
        plt.ylabel('Load held (kg)')
        plt.xlabel('Time [sec]')
        plt.title('Loads held throughout experiment')
        plt.grid()
        plt.legend()

        plt.subplots_adjust(hspace=0.35)
        plt.show()

        load_data_summed = [[t[i], y[i]] for i in range(len(y))]

    elif load_type == "glasses":
        markers = []
        with(open(load_csv, "r") as file):
            lines = file.readlines()
            header = lines[:7]

            srate_line = next(line for line in lines if "SRate" in line).strip().split(": ")[1]
            srate_glasses = int(srate_line[:-2])     #sample rate of glasses in Hz
            start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1][0:-1]
            start_time_load = parse_time(start_time_line)
            

            #read load data for each csv file
            for line in lines[8:]:
                parts = line.strip().split(",")
                time_str = parts[0]
                if "." not in time_str:
                    time_str += ".0"
                time_seconds = parse_time(time_str)
                markers.append([time_seconds-start_time_load, int(parts[1])])

        plt.plot([markers[i][0] for i in range(len(markers))], [markers[i][1] for i in range(len(markers))], 'bo')
        plt.ylabel('Marker ID')
        plt.xlabel('Time [s]')
        plt.title('Detected markers')
        plt.show()

        load_table = {0:[2.6,False],1:[1.9,False],2:[1.9,False],3:[1.9,False],4:[1.9,False],5:[1.9,False],6:[1.2,False],7:[1.2,False],8:[2.6,False],9:[5,False],10:[7.5,False],11:[10,False],23:[0.5,False]}     #table of loads associated with each marker [marker id, weight in kg, picked up?]
        selection_delay = 2     #time in seconds needed to look at a marker to select an object
        detected_id = deque([-1]*(selection_delay*srate_glasses-1))

        load_data_summed = []
        for i in range(len(markers)):
            detected_id.rotate(-1)
            detected_id[-1] = markers[i][1]
            if i == 0:
                load_data_summed.append([markers[i][0], 0])   #set initial load to 0
                continue
            if detected_id == deque([detected_id[-1]]*(selection_delay*srate_glasses-1)) and detected_id[-1] != -1:     #check if detected id has been selected (has been looked at for required delay)
                if load_table[detected_id[-1]][1]:      #check if load has been picked up before or not
                    load_data_summed.append([markers[i][0], load_data_summed[-1][1]-load_table[detected_id[-1]][0]])    #subtract load if it has been picked up before
                else:
                    load_data_summed.append([markers[i][0], load_data_summed[-1][1]+load_table[detected_id[-1]][0]])    #add if not
                load_table[detected_id[-1]][1] = not load_table[detected_id[-1]][1]     #toggle load picked up status
            else:
                load_data_summed.append([markers[i][0], load_data_summed[-1][1]])   #keep load the same if none selected

    #load position data (HEADERS ARE WRONG!!!)
    pos_data = []

    with open(pos_csv, "r") as file:
        lines = file.readlines()

        start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1]
        start_time = parse_time(start_time_line)

        previous_time = None
        for line in lines[8:]:
            parts = line.strip().split(",")
            time_str = parts[0]                     #timestamp
            pos = [float(i) for i in parts[1:]]     #position values
            time_seconds = parse_time(time_str)
            if previous_time is not None:
                duration = time_seconds - previous_time
            else:
                duration = 0  # First line, so duration is 0
            pos.insert(0,time_seconds-start_time)
            pos_data.append(pos)
            previous_time = time_seconds

    print("total distance traveled: ", find_distance_carried(load_data_summed, pos_data))

    #split load data into events where certain object is held with constant weight
    load_split_tolerance = 0.2
    load_data_split = split_into_sublists(load_data_summed, load_split_tolerance)

    #visualise split up load events
    red = False
    for load_event in load_data_split:
        x,y = zip(*load_event)
        plt.plot(x, y, "r-" if red else "b-")
        red = not red

    plt.ylabel('Load held [kg]')
    plt.xlabel('Time [s]')
    plt.title('Split up load events')
    plt.show()

    red = True
    #split each load event into sections of carrying/repositioning or holding
    carrying = []
    carrying_min_distance = 1
    carrying_continuation_distance = 0.07  # Minimum distance threshold to continue walking
    carrying_duration = 2
    pos_index = 0
    pos_data_timestamps = [i[0] for i in pos_data]
    for event_index in range(len(load_data_split)):
        t0 = load_data_split[event_index][0][0]
        distance = 0
        pos_index = bisect.bisect_left(pos_data_timestamps,load_data_split[event_index][0][0],pos_index)    #finds index of pos_data to insert load timestamp into so that it stays sorted, i.e. index of element with timestamp closest to that of load
        if pos_index >= len(pos_data):
            pos_index -= 1
        previous_pos = [[pos_data[pos_index][46], pos_data[pos_index][47]],[pos_data[pos_index][58], pos_data[pos_index][59]]]   #calculate left and right leg position
        start_index = 0
        carrying_event = []
        carrying_started = False
        i = 1
        red = not red
        while i < len(load_data_split[event_index]):
            load = load_data_split[event_index][i]
            duration = load[0] - t0
            pos_index = bisect.bisect(pos_data_timestamps,load[0],pos_index)
            if pos_index >= len(pos_data):
                pos_index -= 1
            current_pos = [[pos_data[pos_index][46], pos_data[pos_index][47]],[pos_data[pos_index][58], pos_data[pos_index][59]]]
            step_distance = max([math.sqrt(sum([(current_pos[k][j] - previous_pos[k][j])**2 for j in range(2)])) for k in range(2)])        #calculate how much legs has moved since last sample
            distance += step_distance
            plt.plot(load[0],distance,"ro" if red else "bo")        #plot distance travelled by legs
            previous_pos = current_pos
            if not carrying_started and duration <= carrying_duration and distance >= carrying_min_distance:
                #if at least min distance travelled in x seconds, subject is assumed to be walking
                carrying_started = True
                carrying_event = [load_data_split[event_index][j] for j in range(start_index,i)]
                del load_data_split[event_index][start_index:i]
                start_index = i
            elif carrying_started and step_distance >= carrying_continuation_distance:
                #if the subject continues walking, add the current load to the carrying event
                carrying_event.append(load_data_split[event_index][i])
                del load_data_split[event_index][i]
                start_index = i
            elif carrying_started and step_distance < carrying_continuation_distance:
                # If the subject stops walking, finalize the current carrying event
                carrying.append(carrying_event)
                carrying_event = []
                carrying_started = False
                start_index = i
                t0 = load[0]
                duration = 0
                distance = 0
            elif duration > carrying_duration:
                #if the subject didn't start walking within the time limit, reset everything
                t0 = load[0]
                duration = 0
                distance = 0
                start_index = i
            i += 1
        
        # Add any remaining carrying_event to the carrying list
        if carrying_event:
            carrying.append(carrying_event)
            # Delete carrying_event from load_data_split
            for load in carrying_event:
                try:
                    load_data_split[event_index].remove(load)
                except ValueError:
                    pass

    plt.ylabel("Leg traveled distance [m]")
    plt.xlabel("Time [s]")
    plt.title("Leg movement")
    plt.show()
    
    repositioning = []
    repositioning_min_distance = 0.2
    repositioning_continuation_distance = 0.05  # Minimum distance threshold to continue repositioning
    repositioning_duration = 0.5
    pos_index = 0
    pos_data_timestamps = [i[0] for i in pos_data]
    for event_index in range(len(load_data_split)):
        t0 = load_data_split[event_index][0][0]
        pos_index = bisect.bisect_left(pos_data_timestamps,load_data_split[event_index][0][0],pos_index)    #finds index of pos_data to insert load timestamp into so that it stays sorted, i.e. index of element with timestamp closest to that of load
        if pos_index >= len(pos_data):
            pos_index -= 1
        previous_pos = [pos_data[pos_index][43:46], pos_data[pos_index][31:34]]   #extract left and right hand position
        distance = 0
        #previous_leg_pos = [[pos_data[pos_index][46], pos_data[pos_index][47]],[pos_data[pos_index][58], pos_data[pos_index][59]]]  # Initial position of the legs
        #leg_distance = 0
        start_index = 0
        repositioning_started = False  # Track whether repositioning has started
        repositioning_event = []
        i = 1
        red = not red
        while i < len(load_data_split[event_index]):
            load = load_data_split[event_index][i]
            duration = load[0] - t0
            pos_index = bisect.bisect(pos_data_timestamps,load[0],pos_index)
            if pos_index >= len(pos_data):
                pos_index -= 1
            current_pos = [pos_data[pos_index][43:46], pos_data[pos_index][31:34]]
            hand_distance = max([math.sqrt(sum([(current_pos[k][j] - previous_pos[k][j])**2 for j in range(3)])) for k in range(2)])  # Distance traveled since the last sample
            distance += hand_distance  # Update distance traveled by hands
            plt.plot(load[0],distance,"ro" if red else "bo")        #plot distance travelled by hands
            previous_pos = current_pos
            #current_leg_pos = [[pos_data[pos_index][46], pos_data[pos_index][47]],[pos_data[pos_index][58], pos_data[pos_index][59]]]
            #step_distance = max([math.sqrt(sum([(current_leg_pos[k][j] - previous_leg_pos[k][j])**2 for j in range(2)])) for k in range(2)])        #calculate how much legs has moved since last sample
            #leg_distance += step_distance
            #previous_leg_pos = current_leg_pos
            if not repositioning_started and duration <= repositioning_duration and (distance >= repositioning_min_distance):
                #if at least x m of hand movement in y seconds, subject is assumed to be repositioning. Gives false positive when moving hand holding no weight, but no way to check this
                repositioning_started = True
                repositioning_event = [load_data_split[event_index][j] for j in range(start_index,i)]
                del load_data_split[event_index][start_index:i]
                start_index = i
            elif repositioning_started and hand_distance >= repositioning_continuation_distance:
                #if the subject continues moving hands, add the current load to the repositioning event
                repositioning_event.append(load_data_split[event_index][i])
                del load_data_split[event_index][i]
                start_index = i
            elif repositioning_started and hand_distance < repositioning_continuation_distance:
                # If the subject stops moving hands, finalize the current repositioning event
                repositioning.append(repositioning_event)
                repositioning_event = []
                repositioning_started = False
                start_index = i
                t0 = load[0]
                duration = 0
                distance = 0
            elif duration > repositioning_duration or load[0] - load_data_split[event_index][i-1][0] > 0.1:
                #if no repositioning was detected during the current window or a gap in the data is detected (e.g. because a carrying event caused a part to be removed), reset everything for a new detection
                t0 = load[0]
                duration = 0
                distance = 0
                start_index = i
            i += 1

        # Add any remaining repositioning_event to the repositioning list
        if repositioning_event:
            repositioning.append(repositioning_event)
            # Delete repositioning_event from load_data_split
            for load in repositioning_event:
                try:
                    load_data_split[event_index].remove(load)
                except ValueError:
                    pass

    plt.ylabel("Hands traveled distance [m]")
    plt.xlabel("Time [s]")
    plt.title("Hand movement")
    plt.show()
    
    holding = load_data_split       #rest of the load events are considered holding events by default

    #visualise carrying, repositioning and holding events
    """for load_event in carrying:
        plt.plot([load_event[i][0] for i in range(len(load_event))], [load_event[i][1] for i in range(len(load_event))], 'r-', label='carrying')
    for load_event in repositioning:
        plt.plot([load_event[i][0] for i in range(len(load_event))], [load_event[i][1] for i in range(len(load_event))], 'g-', label='repositioning')
    for load_event in holding:
        plt.plot([load_event[i][0] for i in range(len(load_event))], [load_event[i][1] for i in range(len(load_event))], 'b-', label='holding')

    plt.ylabel('Load held (kg)')
    plt.xlabel('Time [sec]')
    plt.title('Types of load events')
    plt.legend()
    plt.show()"""

    #find most common posture for each load event
    posture_index = 0
    posture_data_timestamps = [i[0] for i in posture_data]
    for load_event in carrying:
        for load in load_event:
            posture_index = bisect.bisect(posture_data_timestamps,load[0],posture_index)
            if posture_index >= len(posture_data):
                posture_index -= 1
            posture = posture_data[posture_index][1].split("_")
            if posture == ["St","U","FR0","TR0","LB0"]:
                load.append("posture 1")
            elif ("BS" in posture and "TR0" in posture) or ("BF" in posture and "TR0" not in posture) or ("OH" in posture and "TR0" in posture and "LB0" in posture) or (1 < int(posture[2][-1]) < 4) :
                load.append("posture 4")
            elif "Cr" in posture or ("BS" in posture and "TR0" not in posture or "LB0" not in posture) or (int(posture[2][-1]) >= 4):
                load.append("posture 8")
            else:
                load.append("posture 2")
        load_event.append([most_frequent([load[2] for load in load_event])])

    posture_index = 0
    for load_event in repositioning:
        for load in load_event:
            posture_index = bisect.bisect(posture_data_timestamps,load[0],posture_index)
            if posture_index >= len(posture_data):
                posture_index -= 1
            posture = posture_data[posture_index][1].split("_")
            if posture == ["St","U","FR0","TR0","LB0"]:
                load.append("posture 1")
            elif ("BS" in posture and "TR0" in posture) or ("BF" in posture and "TR0" not in posture) or ("OH" in posture and "TR0" in posture and "LB0" in posture) or (1 < int(posture[2][-1]) < 4) :
                load.append("posture 4")
            elif "Cr" in posture or ("BS" in posture and "TR0" not in posture or "LB0" not in posture) or (int(posture[2][-1]) >= 4):
                load.append("posture 8")
            else:
                load.append("posture 2")
        load_event.append([most_frequent([load[2] for load in load_event])])
    
    posture_index = 0
    for load_event in holding:
        for load in load_event:
            posture_index = bisect.bisect(posture_data_timestamps,load[0],posture_index)
            if posture_index >= len(posture_data):
                posture_index -= 1
            posture = posture_data[posture_index][1].split("_")
            if posture == ["St","U","FR0","TR0","LB0"]:
                load.append("posture 1")
            elif ("BS" in posture and "TR0" in posture) or ("BF" in posture and "TR0" not in posture) or ("OH" in posture and "TR0" in posture and "LB0" in posture) or (1 < int(posture[2][-1]) < 4) :
                load.append("posture 4")
            elif "Cr" in posture or ("BS" in posture and "TR0" not in posture or "LB0" not in posture) or (int(posture[2][-1]) >= 4):
                load.append("posture 8")
            else:
                load.append("posture 2")
        load_event.append([most_frequent([load[2] for load in load_event])])


    #find frequency of each repositioning, duration of each holding and distance of each carrying event
    
    carrying_output = []
    processed_indices = set()  # Track indices of events already processed

    for index in range(len(carrying)):
        if index in processed_indices:  # Skip if this event was already processed as an other_event
            continue
        
        load_event = carrying[index]
        reference_weight = np.mean([load_event[i][1] for i in range(len(load_event)-1)])
        distance = find_distance_carried(load_event, pos_data)  # Calculate the distance for the current load_event
        for other_index, other_event in enumerate(carrying[index + 1:], start=index + 1):
            if other_index in processed_indices:  # Skip if already processed
                continue

            if abs(np.mean([other_event[i][1] for i in range(len(other_event)-1)]) - reference_weight) <= load_split_tolerance:      #check if weight is more or less the same
                distance += find_distance_carried(other_event, pos_data)                           #add minimum carrying distance before removing other event
                load_event[-1].append(other_event[-1][0])              #append posture to later determine new most common posture for all events combined
                modified_other_event = other_event + [0]
                modified_other_event[-2] = modified_other_event[-2][0]
                carrying_output.append(modified_other_event)           #add other event to output list with distance 0 so it doesn't affect the eaws calculation, just for visualisation in video
                processed_indices.add(other_index)  # Mark other_event as processed
        load_event[-1] = most_frequent([posture for posture in load_event[-1]])
        load_event.append(distance)
        carrying_output.append(load_event)
        processed_indices.add(index)  # Mark load_event as processed

    carrying_output.sort(key=lambda x:x[0][0])                          #put entries back in chronological order


    holding_output = []
    processed_indices = set()  # Track indices of events already processed

    for i, load_event in enumerate(holding):
        duration = 0
        previous_time = load_event[0][0]
        for sample in load_event[:-1]:                              #last element is the posture
            if sample[0] - previous_time < 0.5:                 #check if samples are more or less consecutive (two holding events with the same load could be separated because of extraction of e.g. carrying event)
                duration += sample[0] - previous_time
                previous_time = sample[0]
            else:
                try:
                    holding.insert(i+1, load_event[load_event.index(sample):])      #if the sample is too far away, it is considered a new event
                except IndexError:
                    holding.append(load_event[load_event.index(sample):])
                holding[i] = load_event[:load_event.index(sample)+1] + [load_event[-1]]      #update current event to only include samples before the new event (also include posture)
                break
        holding[i].append(duration/60)                          #duration is in min/shift

    #combine durations of holding events where same load is carried

    for index in range(len(holding)):
        if index in processed_indices:  # Skip if this event was already processed as an other_event
            continue

        load_event = holding[index]
        reference_weight = np.mean([load_event[i][1] for i in range(len(load_event)-2)])
        for other_index, other_event in enumerate(holding[index + 1:], start=index + 1):
            if abs(np.mean([other_event[i][1] for i in range(len(other_event)-2)]) - reference_weight) <= load_split_tolerance:      #check if weight is more or less the same
                if other_index in processed_indices:  # Skip if already processed
                    continue

                load_event[-1] += other_event[-1]           #add durations of both events before removing other event
                load_event[-2].append(other_event[-2][0])              #append posture to later determine new most common posture for all events combined
                modified_other_event = other_event
                modified_other_event[-2] = modified_other_event[-2][0]
                modified_other_event[-1] = 0             #set duration to 0 for other event so it doesn't affect the eaws calculation
                holding_output.append(modified_other_event)             #add other event to output list with duration 0 so it doesn't affect the eaws calculation, just for visualisation in video
                processed_indices.add(other_index)  # Mark other_event as processed
        load_event[-2] = most_frequent([posture for posture in load_event[-2]])
        holding_output.append(load_event)
        processed_indices.add(index)  # Mark load_event as processed

    holding_output.sort(key=lambda x:x[0][0])

    repositioning_output = []
    processed_indices = set()  # Track indices of events already processed

    for index in range(len(repositioning)):
        if index in processed_indices:  # Skip if this event was already processed as an other_event
            continue

        load_event = repositioning[index]
        reference_weight = np.mean([load_event[i][1] for i in range(len(load_event)-1)])
        frequency = 1
        for other_index, other_event in enumerate(repositioning[index + 1:], start=index + 1):
            if other_index in processed_indices:  # Skip if already processed
                continue

            if abs(np.mean([other_event[i][1] for i in range(len(other_event)-1)]) - reference_weight) <= load_split_tolerance/5:      #check if weight is more or less the same
                frequency += 1                              #increment frequency of event before removing other event
                load_event[-1].append(other_event[-1][0])              #append posture to later determine new most common posture for all events combined
                modified_other_event = other_event + [0]        #set frequency to 0 for other event so it doesn't affect the eaws calculation
                modified_other_event[-2] = modified_other_event[-2][0]
                repositioning_output.append(modified_other_event)      #add other event to output list with frequency 0 so it doesn't affect the eaws calculation, just for visualisation in video
                processed_indices.add(other_index)  # Mark other_event as processed
        load_event[-1] = most_frequent([posture for posture in load_event[-1]])
        load_event.append(frequency)
        repositioning_output.append(load_event)
        processed_indices.add(index)  # Mark load_event as processed

    repositioning_output.sort(key=lambda x:x[0][0])

    #simplify each load event and combine them into one array to feed into physical_load script
    load_output = []

    for load_event in carrying_output:
        time = str(datetime.timedelta(seconds = load_event[0][0] + start_time_load))
        load_output.append({"type": "carrying", "transport": None, "weight": np.mean([load_event[i][1] for i in range(len(load_event)-2)]), "posture": int(load_event[-2].split(" ")[1]), "conditions": 0, "frequency": 0, "duration": 0, "distance": load_event[-1], "time": time})

    for load_event in repositioning_output:
        time = str(datetime.timedelta(seconds = load_event[0][0] + start_time_load))
        load_output.append({"type": "repositioning", "transport": None, "weight": np.mean([load_event[i][1] for i in range(len(load_event)-2)]), "posture": int(load_event[-2].split(" ")[1]), "conditions": 0, "frequency": load_event[-1], "duration": 0, "distance": 0, "time": time})

    for load_event in holding_output:
        time = str(datetime.timedelta(seconds = load_event[0][0] + start_time_load))
        load_output.append({"type": "holding", "transport": None, "weight": np.mean([load_event[i][1] for i in range(len(load_event)-2)]), "posture": int(load_event[-2].split(" ")[1]), "conditions": 0, "frequency": 0, "duration": load_event[-1], "distance": 0, "time": time})

    load_output.sort(key=lambda x:x["time"])
    
    #write loads to file
    type = "AutoDeLoad"
    name = base_filename + " - " + type

    with open(name + ".csv", "w") as file:
        for row in header:
            file.write(row)
        file.write("type,transport,weight (kg),posture,conditions,frequency (#/shift),duration (min/shift),distance (m/shift),time (HH:mm:ss.fff)\n")
        for load in load_output:
            file.write(",".join([str(i) for i in load.values()]))
            file.write("\n")

        

if __name__ == "__main__":
    main()
