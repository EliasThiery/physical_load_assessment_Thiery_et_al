from eaws_score import EAWSScore
from KIM_score import KIMScore
from participant import Operator
from task import Task

import datetime
import cv2
import json
import bisect
import copy

class PhysicalLoad:
    def __init__(self, score_type, posture_csv, load_csv, operator, task):
        self.score_type = score_type
        self.posture_csv = posture_csv
        self.load_csv = load_csv
        self.operator = operator
        self.task = task
        self.score = 0
        self.posture_data, total_duration = self.load_posture_data()
        self.task.duration = total_duration
        self.load_data = self.load_load_data()

    def calculate_TLX_score(self, TLX_csv):
        with open(TLX_csv,"r") as f:
            TLX_data = f.readlines()[1:]

        #find line with name of subject
        for line in TLX_data:
            if line.split(",")[1] == self.operator.name and line.split(",")[2] == self.task.name:
                scores = line.split(",")
                break
        score = sum([int(i)*10 for i in [scores[4], scores[5], scores[7]]])/3
        return score
    
    def calculate_baseline_score(self, baseline_csv):
        with open(baseline_csv,"r") as f:
            data = f.readlines()[1:]

        #find line with name of subject
        for line in data:
            if line.split(",")[1] == self.operator.name:
            #if line.split(",")[1][1:-1] == "John Doe":
                scores = line.split(",")
                break
        score = 0

        #convert multiple choice answers to score values
        for i in [78,88,89,91]:
            score += self.agreement_to_score(scores[i])
        score += self.temporal_long_to_score(scores[97])
        for i in range(118,128):
            score += self.temporal_short_to_score(scores[i])
        score /= 16     #calculate average of scores
        return score
    
    def temporal_short_to_score(self, choice):
        if choice == "Nooit":
            return 0
        elif choice == "Soms":
            return 33
        elif choice == "Vaak":
            return 66
        elif choice == "Altijd":
            return 100
        return 0
    
    def temporal_long_to_score(self, choice):
        if choice == "Nooit":
            return 0
        elif choice == "Sporadisch":
            return 17
        elif choice == "Af en toe":
            return 33
        elif choice == "Regelmatig":
            return 50
        elif choice == "Dikwijls":
            return 67
        elif choice == "Zeer dikwijls":
            return 83
        elif choice == "Altijd":
            return 100
        return 0
    
    def temporal_long_to_score(self, choice):
        if choice == "Nooit":
            return 0
        elif choice == "Sporadisch":
            return 17
        elif choice == "Af en toe":
            return 33
        elif choice == "Regelmatig":
            return 50
        elif choice == "Dikwijls":
            return 67
        elif choice == "Zeer dikwijls":
            return 83
        elif choice == "Altijd":
            return 100
        return 0
    
    def agreement_to_score(self, choice):
        if choice == "Helemaal mee oneens":
            return 0
        elif choice == "Mee oneens":
            return 25
        elif choice == "Noch eens, noch oneens":
            return 50
        elif choice == "Mee eens":
            return 75
        elif choice == "Helemaal mee eens":
            return 100
        return 0

    def calculate_score(self):
        if self.score_type == "EAWS":
            #hardcoded extra points categories, could be passed by production context
            #0d (joint position wrist) could be detected from hum_joint_angles
            extra_loads = [
                {"type": "0a", "intensity": 0},
                {"type": "0b", "intensity": 0},
                {"type": "0c", "intensity": 0, "frequency": 0},
                {"type": "0d", "intensity": 0, "frequency": 0},
                {"type": "0e", "intensity": 0},
            ]
            eaws = EAWSScore(self.operator, self.task, self.posture_data, (copy.deepcopy(self.load_data)))
            eaws.calculate_whole_body_extra_points(extra_loads)
            eaws.calculate_posture_score()
            print("Posture score: ", eaws.postures_score)
            eaws.calculate_loads(copy.deepcopy(self.load_data))
            print("Loads score: ", eaws.loads_score)
            self.score = eaws.calculate_eaws_score()
            return self.score
        elif self.score_type == "KIM":
            kim = KIMScore(self.operator, self.task, self.posture_data, (copy.deepcopy(self.load_data)))
            kim.calculate_ABP()
            kim.calculate_LHC(copy.deepcopy(self.load_data))
            self.score = kim.calculate_KIM_score()
            return self.score
        else:
            raise ValueError("Unknown score type")
        
    def calculate_intermediate_score(self, time, index):
        if self.score_type == "EAWS":
            #hardcoded extra points categories, could be passed by production context
            #0d (joint position wrist) could be detected from hum_joint_angles
            extra_loads = [
                {"type": "0a", "intensity": 0},
                {"type": "0b", "intensity": 0},
                {"type": "0c", "intensity": 0, "frequency": 0},
                {"type": "0d", "intensity": 0, "frequency": 0},
                {"type": "0e", "intensity": 0},
            ]
            eaws = EAWSScore(self.operator, self.task, self.posture_data, copy.deepcopy(self.load_data))
            eaws.calculate_whole_body_extra_points(extra_loads)
            eaws.calculate_loads(copy.deepcopy(self.load_data), index)
            return eaws.calculate_intermediate_eaws_score(time, index)
        elif self.score_type == "KIM":
            kim = KIMScore(self.operator, self.task, self.posture_data, copy.deepcopy(self.load_data))
            kim.calculate_LHC(copy.deepcopy(self.load_data), index)
            return kim.calculate_intermediate_KIM_score(time, index)
        else:
            raise ValueError("Unknown score type")

    def load_posture_data(self):
        with open(self.posture_csv, 'r') as file:
            lines = file.readlines()
            # Find and parse the start and end times
            start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1]
            end_time_line = next(line for line in lines if "End time" in line).strip().split(": ")[1].split()[1]
            
            start_time = self.parse_time(start_time_line)
            end_time = self.parse_time(end_time_line)
            total_duration = end_time - start_time

            if start_time is None or end_time is None:
                raise ValueError("Invalid start or end time format")


            # Read posture data
            posture_data = []
            previous_time = None
            for line in lines[8:-1]:
                parts = line.strip().split(",")
                time_str = parts[0]
                posture = parts[1]
                time_seconds = self.parse_time(time_str)
                if previous_time is not None:
                    duration = time_seconds - previous_time
                else:
                    duration = 0  # First line, so duration is 0
                    
                posture_data.append({"timestamp": time_seconds-start_time, "time": duration, "posture": posture})
                previous_time = time_seconds
        
        return posture_data, total_duration

    def load_load_data(self):
        load_data = []

        with open(self.load_csv, "r") as file:
            lines = file.readlines()
            start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1]
            start_time = self.parse_time(start_time_line)

            for line in lines[8:]:
                data = line.split(",")
                time = data[8].strip()
                load_data.append({"type": data[0], "transport": data[1], "weight": float(data[2]), "posture": int(data[3]), "conditions": int(data[4]), "frequency": int(data[5]), "duration": float(data[6]), "distance": float(data[7]), "time": float(self.parse_time(time))-start_time})
        
        return load_data
    
    def parse_time(self, time_str):
        time_format = "%H:%M:%S.%f"
        try:
            if "." not in time_str:
                time_str += ".0"
            parsed_time = datetime.datetime.strptime(time_str, time_format)
            total_seconds = parsed_time.hour * 3600 + parsed_time.minute * 60 + parsed_time.second + parsed_time.microsecond / 1e6
            return total_seconds
        except ValueError:
            return None
    
    def save_physical_scores_to_file(self):
        #get start time and end time from posture data
        with open(self.posture_csv, 'r') as file:
            lines = file.readlines()
            header = lines[:7]
            # Find and parse the start and end times
            start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1]
            end_time_line = next(line for line in lines if "End time" in line).strip().split(": ")[1].split()[1]
            
            start_time = self.parse_time(start_time_line)
            end_time = self.parse_time(end_time_line)

            if start_time is None or end_time is None:
                raise ValueError("Invalid start or end time format")

        baseline_score = self.calculate_baseline_score("Wellficiency_baseline_survey.csv")
        NASA_TLX_score = self.calculate_TLX_score("Wellficiency_NASA_TLX.csv")

        #write EAWS scores to file
        scores = []
        for index, posture in enumerate(self.posture_data):
            whole_body_extra_score, posture_score, loads_score, eaws_score = self.calculate_intermediate_score(posture["timestamp"], index)
            scores.append([str(datetime.timedelta(seconds = posture["timestamp"] + start_time)), eaws_score, whole_body_extra_score, posture_score, 0, loads_score, 0, baseline_score, NASA_TLX_score])

        filename = self.posture_csv.split(" ")[0] + "_EAWS.csv"

        with open(filename,"w") as file:
            file.write("Name: Physical Score\nType: EAWS\nChannels: 9\nSRate: unknown\n" + header[-3] + header[-2] + "\n")
            file.write("time [HH:mm:ss.fff],EAWS score,whole body extra score,posture score,forces score,loads score,upper limbs score,baseline score,NASA TLX score\n")
            for score in scores:
                file.write(",".join([str(i) for i in score])+"\n")

        #write KIM scores to file
            self.score_type = "KIM"
            scores = []
            for index, posture in enumerate(self.posture_data):
                kim_scores = self.calculate_intermediate_score(posture["timestamp"], index)
                scores.append([str(datetime.timedelta(seconds = posture["timestamp"] + start_time))] + sum([[kim_scores[i][0], kim_scores[i][1]] for i in range(len(kim_scores))],[]) + [baseline_score, NASA_TLX_score])

        filename = self.posture_csv.split(" ")[0] + "_KIM.csv"

        with open(filename,"w") as file:
            file.write("Name: Physical Score\nType: KIM\nChannels: 15\nSRate: unknown\n" + header[-3] + header[-2] + "\n")
            file.write("time [HH:mm:ss.fff],time rating MHO, intensity MHO,time rating ABP,intensity ABP,time rating BM,intensity BM,time rating BF,intensity BF,time rating LHC,intensity LHC,time rating PP,intensity PP,baseline score,NASA TLX score\n")
            for score in scores:
                file.write(",".join([str(i) for i in score])+"\n")
        
        self.score_type = "EAWS"

        print("Scores saved to file.")

    def process_video_with_posture(self, input_vid_filepath, output_vid_filepath):        
        #get start time and end time from posture data
        with open(self.posture_csv, 'r') as file:
            lines = file.readlines()
            header = lines[:7]
            # Find and parse the start and end times
            start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1]
            end_time_line = next(line for line in lines if "End time" in line).strip().split(": ")[1].split()[1]
            
            start_time = self.parse_time(start_time_line)
            end_time = self.parse_time(end_time_line)

            if start_time is None or end_time is None:
                raise ValueError("Invalid start or end time format")

        baseline_score = self.calculate_baseline_score("Wellficiency_baseline_survey.csv")
        NASA_TLX_score = self.calculate_TLX_score("Wellficiency_NASA_TLX.csv")

        #write EAWS scores to file
        scores = []
        for index, posture in enumerate(self.posture_data):
            whole_body_extra_score, posture_score, loads_score, eaws_score = self.calculate_intermediate_score(posture["timestamp"], index)
            scores.append([str(datetime.timedelta(seconds = posture["timestamp"] + start_time)), eaws_score, whole_body_extra_score, posture_score, 0, loads_score, 0, baseline_score, NASA_TLX_score])

        filename = self.posture_csv.split(" ")[0] + "_EAWS.csv"

        with open(filename,"w") as file:
            file.write("Name: Physical Score\nType: EAWS\nChannels: 9\nSRate: unknown\n" + header[-3] + header[-2] + "\n")
            file.write("time [HH:mm:ss.fff],EAWS score,whole body extra score,posture score,forces score,loads score,upper limbs score,baseline score,NASA TLX score\n")
            for score in scores:
                file.write(",".join([str(i) for i in score])+"\n")

        #write KIM scores to file
            self.score_type = "KIM"
            scores = []
            for index, posture in enumerate(self.posture_data):
                kim_scores = self.calculate_intermediate_score(posture["timestamp"], index)
                scores.append([str(datetime.timedelta(seconds = posture["timestamp"] + start_time))] + sum([[kim_scores[i][0], kim_scores[i][1]] for i in range(len(kim_scores))],[]) + [baseline_score, NASA_TLX_score])

        filename = self.posture_csv.split(" ")[0] + "_KIM.csv"

        with open(filename,"w") as file:
            file.write("Name: Physical Score\nType: KIM\nChannels: 15\nSRate: unknown\n" + header[-3] + header[-2] + "\n")
            file.write("time [HH:mm:ss.fff],time rating MHO,intensity MHO,time rating ABP,intensity ABP,time rating BM,intensity BM,time rating BF,intensity BF,time rating LHC,intensity LHC,time rating PP,intensity PP,baseline score,NASA TLX score\n")
            for score in scores:
                file.write(",".join([str(i) for i in score])+"\n")
        
        self.score_type = "EAWS"

        print("Scores saved to file.")
        
        # Open the video capture object
        cap = cv2.VideoCapture(input_vid_filepath)

        # Check if video opened successfully
        if not cap.isOpened():
            print("Error opening video!")
            return

        # Define text properties
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_thickness = 1
        text_color = (255, 255, 255)  # White color in BGR format
        text_bg_color = (0, 0, 0)  # Black background color

        # Get video properties for output video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Adjust fourcc for different codecs (e.g., MP4: 'XVID')
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create video writer object with the obtained properties
        out = cv2.VideoWriter(output_vid_filepath, fourcc, fps, (frame_width, frame_height))

        cumulative_duration_posture = 0 # TODO: Change Delay between beginning of video and beginning of recording (when pressing record in datamanager)
        current_posture_index = 0
        closest_posture = None
        cumulative_duration_load = 0
        current_load_index = 0
        closest_load = None

        while True:
            # Capture frame-by-frame
            frame_exists, frame = cap.read()

            if not frame_exists:
                break

            # Calculate elapsed time
            elapsed_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            #Find the posture for which the timestamp is closest to and below the elapsed time
            posture_data_timestamps = [i["timestamp"] for i in self.posture_data]
            current_posture_index = max(0, bisect.bisect_left(posture_data_timestamps,elapsed_time,current_posture_index)-1)
            if current_posture_index >= len(self.posture_data):
                current_posture_index -= 1
            closest_posture = self.posture_data[current_posture_index]
            cumulative_duration_posture = closest_posture['timestamp']

            #same for load
            load_data_timestamps = [i["time"] for i in self.load_data]
            current_load_index = max(0, bisect.bisect_left(load_data_timestamps,elapsed_time,current_load_index)-1)
            if current_load_index >= len(self.load_data):
                current_load_index -= 1
            closest_load = self.load_data[current_load_index]
            
            text = f"Timestamp: {elapsed_time}"[:-4]

            text_size = cv2.getTextSize(text, font_face, font_scale, font_thickness)[0]
            cv2.rectangle(frame, (10, 25 - text_size[1]), (10 + text_size[0], 25), text_bg_color, -1)
            cv2.putText(frame, text, (10, 25), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
            
            if closest_posture is not None and closest_load is not None:
                # Overlay closest posture and corresponding timestamp
                posture_text = f"Posture: {closest_posture['posture']}"
                # Draw a filled rectangle as background for the text
                text_size = cv2.getTextSize(posture_text, font_face, font_scale, font_thickness)[0]
                cv2.rectangle(frame, (10, 50 - text_size[1]), (10 + text_size[0], 50), text_bg_color, -1)
                cv2.putText(frame, posture_text, (10, 50), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                whole_body_extra_score, posture_score, loads_score, eaws_score = self.calculate_intermediate_score(cumulative_duration_posture, current_posture_index)
                eaws_text = f"Whole body extra points: {whole_body_extra_score}"
                text_size = cv2.getTextSize(eaws_text, font_face, font_scale, font_thickness)[0]
                cv2.rectangle(frame, (10, 75 - text_size[1]), (10 + text_size[0], 75), text_bg_color, -1)
                cv2.putText(frame, eaws_text, (10, 75), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                eaws_text = f"Posture score: {posture_score}"
                text_size = cv2.getTextSize(eaws_text, font_face, font_scale, font_thickness)[0]
                cv2.rectangle(frame, (10, 100 - text_size[1]), (10 + text_size[0], 100), text_bg_color, -1)
                cv2.putText(frame, eaws_text, (10, 100), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                eaws_text = f"Load score: {loads_score}"
                text_size = cv2.getTextSize(eaws_text, font_face, font_scale, font_thickness)[0]
                cv2.rectangle(frame, (10, 125 - text_size[1]), (10 + text_size[0], 125), text_bg_color, -1)
                cv2.putText(frame, eaws_text, (10, 125), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                eaws_text = f"Load: {closest_load['weight']} kg; {closest_load['type']}"
                text_size = cv2.getTextSize(eaws_text, font_face, font_scale, font_thickness)[0]
                cv2.rectangle(frame, (10, 150 - text_size[1]), (10 + text_size[0], 150), text_bg_color, -1)
                cv2.putText(frame, eaws_text, (10, 150), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                eaws_text = f"EAWS: {eaws_score}"
                text_size = cv2.getTextSize(eaws_text, font_face, font_scale, font_thickness)[0]
                cv2.rectangle(frame, (10, 175 - text_size[1]), (10 + text_size[0], 175), text_bg_color, -1)
                cv2.putText(frame, eaws_text, (10, 175), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                self.score_type = "KIM"
                KIM_scores = self.calculate_intermediate_score(cumulative_duration_posture, current_posture_index)
                KIM_score = sum([KIM_scores[i][0]*KIM_scores[i][1] for i in range(len(KIM_scores))])
                kim_text = f"KIM: {KIM_score}"
                text_size = cv2.getTextSize(kim_text, font_face, font_scale, font_thickness)[0]
                cv2.rectangle(frame, (10, 200 - text_size[1]), (10 + text_size[0], 200), text_bg_color, -1)
                cv2.putText(frame, kim_text, (10, 200), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                self.score_type = "EAWS"
                

            # Display the resulting frame
            cv2.imshow('Video with Posture', frame)

            # Write the frame to the output video
            out.write(frame)

            # Wait for key press
            key = cv2.waitKey(1)
            if key == ord('q'):
                break
            

        # Release the video capture object and close all windows
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        print(f"Video with posture saved to: {output_vid_filepath}")



if __name__ == "__main__":
    #score_type = input("Enter score type (EAWS/KIM): ").upper()
    #posture_csv = input("Enter path to posture data CSV file: ")
    operator1 = Operator("John Doe", "M", 185, 65)
    task = Task('Palletizing of weights')
    operation = "video"
    physical_load = PhysicalLoad("EAWS", "sess1_JohnD - AutoDePos.csv", "sess1_JohnD - AutoDeLoad.csv", operator1, task)
    print("Score:", physical_load.calculate_score())
    print("baseline survey score: ", physical_load.calculate_baseline_score("Wellficiency_baseline_survey.csv"))
    print("NASA TLX score: ", physical_load.calculate_TLX_score("Wellficiency_NASA_TLX.csv"))
    if operation == "video":

        physical_load.process_video_with_posture("sess1_JohnD.mp4", "output_sess1_JohnD.mp4")
    elif operation == "files":
        physical_load.save_physical_scores_to_file()