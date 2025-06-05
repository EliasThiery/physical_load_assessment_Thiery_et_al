import bisect
import math

class KIMScore:
    def __init__(self, operator, task, postures, loads):
        self.participant_name = operator.name
        
        self.task_name = task.name
        self.total_duration = task.duration
        self.operator_gender = operator.gender
        self.body_weight = operator.weight
        self.postures = postures
        self.loads = loads

        # Initialize scores
        self.MHO_score = [0,0]      #[time rating, score]
        self.ABP_score = [0,0]
        self.BM_score = [0,0]
        self.BF_score = [0,0]
        self.LHC_score = [0,0]
        self.PP_score = [0,0]

    def calculate_nonlinear_time_rating(self, duration):
        return 0.56 + 0.44*duration**0.5    #duration in minutes

    def calculate_MHO(self):
        # Placeholder for calculating manual handling operations score
        pass


    def calculate_ABP(self, duration=None, index=None):
        time_rating = self.total_duration/3600

        if index is not None:
            postures = self.postures[:index]
        else:
            postures = self.postures

        load_timestamps = [load["time"] for load in self.loads]

        score_A = 0
        load_index = 0
        durations = [0]*6   #last duration is for twisting/bending in unfavorable working conditions
        for posture in postures:
            load_index = bisect.bisect(load_timestamps,posture["timestamp"],load_index)     #find index of load event closest in time to current posture
            if load_index >= len(self.loads):
                load_index -= 1
            if self.loads[load_index]["weight"] > 3:                                        #ABP score is not considered for loads greater than 3 kg (use LHC instead)
                continue
            if "U" in posture["posture"]:               #upright back posture
                durations[0] += posture["time"]
            elif "BF" in posture["posture"]:            #moderately inclined forward
                durations[1] += posture["time"]
            elif "BS" in posture["posture"]:            #strongly inclined forward
                durations[2] += posture["time"]
            elif "Cr_BS" in posture["posture"]:         #"forced postures", not sure how to detect that
                durations[3] += posture["time"]
            if int(posture["posture"][-1]) >= 2 or int(posture["posture"][-5]) >= 2:    #check if severe lateral bending or trunk rotation is present
                durations[-1] += posture["time"]
            #sitting in variable posture very difficult to detect

        #score for postures A
        score_A += math.ceil(durations[0]/self.total_duration*4)*2
        if 0 < durations[1] < self.total_duration/4:
            score_A += 7
        elif durations[1] < self.total_duration/2:
            score_A += 15
        elif durations[1] < 3*self.total_duration/4:
            score_A += 22
        elif durations[1] >= 3*self.total_duration/4:
            score_A += 30

        score_A += math.ceil(durations[2]/self.total_duration*4)*10
        score_A += math.ceil(durations[3]/self.total_duration*4)*3

        score_B = 0
        load_index = 0
        durations = [0]*5 + durations[-1:]   #last duration is for twisting/bending in unfavorable working conditions
        for posture in postures:
            load_index = bisect.bisect(load_timestamps,posture["timestamp"],load_index)     #find index of load event closest in time to current posture
            if load_index >= len(self.loads):
                load_index -= 1
            if self.loads[load_index]["weight"] > 3:                                        #ABP score is not considered for loads greater than 3 kg (use LHC instead)
                continue
            if "OS" in posture["posture"] or "OH" in posture["posture"]:        #hands above shoulders or head
                durations[0] += posture["time"]
            elif int(posture["posture"][-9]) >= 1:   #arms below shoulders level but away from body, #very difficult to detect unsupported arms
                durations[1] += posture["time"]
            elif "Ly" in posture["posture"] and ("OH" in posture["posture"] or int(posture["posture"][-9] >= 2)):     #lying on back with hands over head or lying on stomach with hands below body (not sure how to detect last one)
                durations[2] += posture["time"]
            if int(posture["posture"][-1]) >= 2 or int(posture["posture"][-5]) >= 2:    #check if severe lateral bending or trunk rotation is present
                durations[-1] += posture["time"]

        #score for postures B
        score_B += math.ceil(durations[0]/self.total_duration*4)*10
        score_B += math.ceil(durations[2]/self.total_duration*4)*7

        score_C = 0
        load_index = 0
        durations = [0]*5 + durations[-1:]  #last duration is for twisting/bending in unfavorable working conditions
        for posture in postures:
            load_index = bisect.bisect(load_timestamps,posture["timestamp"],load_index)     #find index of load event closest in time to current posture
            if load_index >= len(self.loads):
                load_index -= 1
            if self.loads[load_index]["weight"] > 3:                                        #ABP score is not considered for loads greater than 3 kg (use LHC instead)
                continue
            if "St" in posture["posture"]:        #constant standing
                durations[0] += posture["time"]
            #very difficult to detect unsupported arms
            elif "Cr" in posture["posture"]:     #kneeling, squatting or sitting cross-legged (not sure how to detect that last one)
                durations[2] += posture["time"]
            if int(posture["posture"][-1]) >= 2 or int(posture["posture"][-5]) >= 2:    #check if severe lateral bending or trunk rotation is present
                durations[-1] += posture["time"]

        #score for postures C
        score_C += math.ceil(durations[0]/self.total_duration*4)*2
        score_C += math.ceil(durations[1]/self.total_duration*4)*10

        posture_score = [score_A, score_B, score_C]

        unfavorable_working_conditions = [0,0,0] #[A,B,C]

        #score for twisting/lateral bending
        if 0 < durations[-1] < self.total_duration/4:
            unfavorable_working_conditions[0] += 1
        elif durations[-1] >= self.total_duration/4:
            unfavorable_working_conditions[0] += 2
            unfavorable_working_conditions[2] += 1

        #other unfavorable working condition scores very difficult to detect with current sensors

        further_working_conditions = [0,0,0] #[A,B,C], impossible to detect, task-specific

        score = [posture_score[i] + unfavorable_working_conditions[i] + further_working_conditions[i] for i in range(3)]

        self.ABP_score = [time_rating, max(score)]


    def calculate_BM(self):
        # Placeholder for calculating body movement score
        pass


    def calculate_BF(self):
        # Placeholder for calculating body forces score
        pass

    def calculate_LHC(self, loads_input, index=None):
        #calculate time rating using non-linear formula
        time_rating = self.calculate_nonlinear_time_rating(self.total_duration/60)

        #Find end index of loads based on that of posture
        if index is not None:
            if index >= len(self.postures):
                print("reached end")
                return 0
            end_time = self.postures[index-1]["timestamp"]
            for i in range(len(self.loads)):
                if self.loads[i]["time"] >= end_time:
                    loads = self.loads[:i+1]
                    break
                else:
                    loads = self.loads
        else:
            index = len(self.postures)
            loads = self.loads

        for load in loads:
            if load["frequency"] == 0 and load["duration"] == 0 and load["distance"] == 0:
                loads.remove(load)

        if not loads:
            return
       
        load_rating_points = 0
        effective_load_weight = max([load["weight"] for load in loads])     #"typical" load weight interpreted as maximum load weight
            
        #load rating score
        if self.operator_gender == "M":
            if 3 <= effective_load_weight <= 5:
                load_rating_points = 4
            elif 5 < effective_load_weight <= 10:
                load_rating_points = 6
            elif 10 < effective_load_weight <= 15:
                load_rating_points = 8
            elif 15 < effective_load_weight <= 20:
                load_rating_points = 11
            elif 20 < effective_load_weight <= 25:
                load_rating_points = 15
            elif 25 < effective_load_weight <= 30:
                load_rating_points = 25
            elif 30 < effective_load_weight <= 35:
                load_rating_points = 35
            elif 35 < effective_load_weight <= 40:
                load_rating_points = 75
            elif effective_load_weight > 40:
                load_rating_points = 100
        else:
            if 3 <= effective_load_weight <= 5:
                load_rating_points = 6
            elif 5 < effective_load_weight <= 10:
                load_rating_points = 9
            elif 10 < effective_load_weight <= 15:
                load_rating_points = 12
            elif 15 < effective_load_weight <= 20:
                load_rating_points = 25
            elif 20 < effective_load_weight <= 25:
                load_rating_points = 75
            elif 25 < effective_load_weight <= 30:
                load_rating_points = 85
            elif effective_load_weight > 30:
                load_rating_points = 100

        load_handling_conditions = 0    #not possible to detect with current sensors (maybe with armband in the future)

        posture_points = 0
        
        posture_index = [0,0]
        posture_timestamps = [posture["timestamp"] for posture in self.postures]
        load_handling_postures = [0]*10     #list of amount of occurences for each type of start/end postures
        for load_index in range(len(loads)-1):
            #find start and end times of load event and corresponding postures
            start_and_end_time = [loads[load_index]["time"], loads[load_index+1]["time"]]
            posture_index = [min(bisect.bisect(posture_timestamps,start_and_end_time[0],posture_index[0]),len(posture_timestamps)-1), min(bisect.bisect(posture_timestamps,start_and_end_time[1],posture_index[1]),len(posture_timestamps)-1)]      #get indices of postures at same time as load events
            #add occurence to type of start/end postures
            #permute indices of postures so both can be seen as start or end
            for i in range(2):
                #first type gives score of 0, so we can ignore it
                if ("St_U" in self.postures[posture_index[i]]["posture"]) and ("St_BF" in self.postures[posture_index[1-i]]["posture"] or "St_OH" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[1] += 1
                elif ("St_BF" in self.postures[posture_index[i]]["posture"] or "St_OH" in self.postures[posture_index[i]]["posture"]) and ("St_BF" in self.postures[posture_index[1-i]]["posture"] or "St_OH" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[2] += 0.5    #will be counted twice because start and end posture are identical
                elif ("St_U" in self.postures[posture_index[i]]["posture"]) and ("St_BS" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[3] += 1
                elif ("St_U" in self.postures[posture_index[i]]["posture"]) and ("Cr" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[4] += 1
                elif ("St_BF" in self.postures[posture_index[i]]["posture"] or "St_OH" in self.postures[posture_index[i]]["posture"]) and ("St_BS" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[5] += 1
                elif ("St_BF" in self.postures[posture_index[i]]["posture"] or "St_OH" in self.postures[posture_index[i]]["posture"]) and ("Cr" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[6] += 1
                elif ("St_BS" in self.postures[posture_index[i]]["posture"]) and ("St_BS" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[7] += 0.5    #will be counted twice because start and end posture are identical
                elif ("St_BS" in self.postures[posture_index[i]]["posture"]) and ("Cr" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[8] += 1
                elif ("Cr" in self.postures[posture_index[i]]["posture"]) and ("Cr" in self.postures[posture_index[1-i]]["posture"]):
                    load_handling_postures[9] += 0.5    #will be counted twice because start and end posture are identical
        
        points = [0,3,5,7,9,10,13,15,18,20]
        for i in range(1, len(points)):
            if load_handling_postures[i]/len(self.loads) > 0.1:   #check if posture is regularly held and not a rare deviation (>10% of load_events are with this posture)
                posture_points += points[i]

        #determining additional points
        additional_points = 0
        durations = [0]*4   #durations of twisting/lateral bending, arm height, etc. for additional points
        for posture in self.postures[:index]:
            if int(posture["posture"][-1]) >= 1 or int(posture["posture"][-5]) >= 1:    #twisting/lateral bending
                durations[0] += posture["time"]
            if int(posture["posture"][-9]) >= 1:     #hands away from the body
                durations[1] += posture["time"]
            #very difficult to hands between elbow and shoulder height
            if "OS" in posture["posture"] or "OH" in posture["posture"]:    #hands above shoulder height
                durations[3] += posture["time"]

        if 0 < durations[0] < self.total_duration/4:
            additional_points += 1
        elif durations[0] >= self.total_duration/4:
            additional_points += 3
        
        if 0 < durations[1] < self.total_duration/4:
            additional_points += 1
        elif durations[1] >= self.total_duration/4:
            additional_points += 3
        
        if 0 < durations[2] < self.total_duration/4:
            additional_points += 0.5
        elif durations[2] >= self.total_duration/4:
            additional_points += 1

        if 0 < durations[3] < self.total_duration/4:
            additional_points += 1
        elif durations[3] >= self.total_duration/4:
            additional_points += 2
        
        posture_points += max(6, additional_points)      #additional points can be max 6
            

        unfavorable_working_conditions = 0  #not possible to detect with current sensors and/or task-specific
        work_organisation_points = 0    #impossible to detect, task-specific
        
        self.LHC_score = [time_rating, load_rating_points + load_handling_conditions + posture_points + unfavorable_working_conditions + work_organisation_points]


    def calculate_PP(self):
        # Placeholder for calculating pushing and pulling score
        pass

    def calculate_KIM_score(self):
        # Calculate the EAWS score as the sum of all sub-scores
        KIM_score = [self.MHO_score, self.ABP_score, self.BM_score, self.BF_score, self.LHC_score + self.PP_score]
        return KIM_score

    def calculate_intermediate_KIM_score(self, intermediate_time, index):
            # Calculate posture score up to the intermediate time
            self.calculate_ABP(intermediate_time, index)
            
            # Calculate the EAWS score as the sum of posture score and other sub-scores
            KIM_score = [self.MHO_score, self.ABP_score, self.BM_score, self.BF_score, self.LHC_score, self.PP_score]
            
            return KIM_score