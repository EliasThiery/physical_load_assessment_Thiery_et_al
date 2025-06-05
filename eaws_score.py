import bisect


class EAWSScore:
    def __init__(self, operator, task, postures, loads):
        self.participant_name = operator.name
        
        self.task_name = task.name
        self.total_duration = task.duration
        self.operator_gender = operator.gender
        self.body_weight = operator.weight
        self.postures = postures
        self.loads = loads

        # Initialize scores
        self.whole_body_extra_points = 0
        self.postures_score = 0
        self.forces_score = 0
        self.loads_score = 0
        self.upper_limbs_score = 0

    def calculate_whole_body_extra_points(self, extra_loads):
            # Iterate through each extra load and calculate the intensity x frequency based on load type
            for load in extra_loads:
                load_type = load["type"]
                intensity = load.get("intensity", 0)
                frequency = load.get("frequency", 0)

                # Perform calculations based on load type
                if load_type == "0a" or load_type == "0b" or load_type == "0e":
                    # For load types 0a, 0b, and 0e, calculate intensity
                    self.whole_body_extra_points += intensity
                elif load_type == "0c":
                    # Calculate score based on frequency mapping
                    if frequency < 1:
                        score = 0
                    elif 1 <= frequency <= 2:
                        score = 1
                    elif 2 < frequency <= 5:
                        score = 2.5
                    elif 5 < frequency <= 10:
                        score = 4
                    elif 10 < frequency <= 20:
                        score = 6
                    else:
                        score = 8
                    # Add score multiplied by intensity to whole_body_extra_points
                    self.whole_body_extra_points += score * intensity
                elif load_type == "0d":
                    # If frequency provided, calculate score based on frequency mapping
                    if frequency:
                        if frequency < 1:
                            score = 0
                        elif 1 <= frequency < 8:
                            score = 2
                        elif 8 <= frequency < 11:
                            score = 2.5
                        elif 11 <= frequency < 16:
                            score = 4
                        elif 16 <= frequency < 20:
                            score = 6
                        else:
                            score = 8
                    # If duration provided, calculate score based on duration mapping
                    else:
                        duration = load.get("duration", 0)
                        if duration < 3:
                            score = 0
                        elif 3 <= duration < 10:
                            score = 2
                        elif 10 <= duration < 20:
                            score = 2.5
                        elif 20 <= duration < 40:
                            score = 4
                        elif 40 <= duration < 60:
                            score = 6
                        else:
                            score = 8
                    # Add score multiplied by intensity to whole_body_extra_points
                    self.whole_body_extra_points += score * intensity
                else:
                    raise ValueError("Unknown load type")


    def find_posture_type(self, posture_string):
        posture_map = {
            "St_U": 1,
            "St_BF": 3,
            "St_BS": 4,
            "St_OS": 5,
            "St_OH": 6,
            "Cr_U": 12,
            "Cr_BF": 13,
            "Cr_OS": 14,
            "Ly": 15
        }
        
        # Iterate through the keys of posture_map
        for key in posture_map:
            if key in posture_string:
                return posture_map[key]  # Return the corresponding value if key is found in posture_string
    
        return None  # Return None if no key is found in posture_string

    def calculate_posture_score(self, duration=None, index=None):
                
        self.postures_score = 0

       # Initialize dictionaries to store accumulated times for prefixes, FRX groups, TRX groups, and LBX groups
        accumulated_times_prefix = {}
        accumulated_times_FRX = {}
        accumulated_times_TRX = {}
        accumulated_times_LBX = {}

        if duration is None:
            duration = self.total_duration

        load_timestamps = [load["time"] for load in self.loads]

        load_index = 0
        index_counter = 0
        # Iterate over the posture data to accumulate time for each prefix, FRX group, TRX group, and LBX group
        for entry in self.postures:
            posture = entry['posture']
            time = entry['time']

            # Check if the entry time exceeds the duration (if provided)
            if(index is not None):
                if index_counter > index:
                    break
            
            load_index = bisect.bisect(load_timestamps,entry["timestamp"],load_index)     #find index of load event closest in time to current posture
            if load_index >= len(self.loads):
                load_index -= 1
            if self.loads[load_index]["weight"] > 3:                                        #posture score is not considered for loads greater than 3 kg (use handled loads instead)
                continue
            
            # Extract the prefix, TRX group, and LBX group from the posture
            prefix = '_'.join(posture.split('_')[:2])
            FRX_group = posture.split('_')[-3]
            TRX_group = posture.split('_')[-2]
            LBX_group = posture.split('_')[-1]
            
            # Accumulate time for each prefix
            if prefix not in accumulated_times_prefix:
                accumulated_times_prefix[prefix] = 0
            accumulated_times_prefix[prefix] += time
            
            # Accumulate time for each FRX group
            if FRX_group not in accumulated_times_FRX:
                accumulated_times_FRX[FRX_group] = 0
            accumulated_times_FRX[FRX_group] += time

            # Accumulate time for each TRX group
            if TRX_group not in accumulated_times_TRX:
                accumulated_times_TRX[TRX_group] = 0
            accumulated_times_TRX[TRX_group] += time

            # Accumulate time for each TRX group
            if TRX_group not in accumulated_times_TRX:
                accumulated_times_TRX[TRX_group] = 0
            accumulated_times_TRX[TRX_group] += time
            
            # Accumulate time for each LBX group
            if LBX_group not in accumulated_times_LBX:
                accumulated_times_LBX[LBX_group] = 0
            accumulated_times_LBX[LBX_group] += time

            index_counter += 1

        # Convert accumulated time dictionaries to lists of dictionaries
        posture_data_A = [{'time': time, 'posture': prefix} for prefix, time in accumulated_times_prefix.items()]
        posture_data_FRX = [{'time': time, 'posture': FRX_group} for FRX_group, time in accumulated_times_FRX.items()]
        posture_data_TRX = [{'time': time, 'posture': TRX_group} for TRX_group, time in accumulated_times_TRX.items()]
        posture_data_LBX = [{'time': time, 'posture': LBX_group} for LBX_group, time in accumulated_times_LBX.items()]

        score_A = 0
        score_B = 0

        #print(posture_data_A)

        # Iterate over each posture in the list
        for posture in posture_data_A:
            # Compute duration_s_min
            duration_s_min = posture['time'] * 60 / duration

            # Calculate score A based on duration_s_min
            score_A = score_A + self.calculate_score_A(self.find_posture_type(posture['posture']), duration_s_min)

        #interpolation between values for FR, LB and TR in EAWS (0,1,3,5)

        for posture in posture_data_FRX:
            # Compute duration_s_min
            duration_s_min = posture['time'] * 60 / duration

            score_B = score_B + int(posture['posture'][-1])*self.far_reach_duration(duration_s_min)

        for posture in posture_data_TRX:
            # Compute duration_s_min
            duration_s_min = posture['time'] * 60 / duration

            score_B = score_B + int(posture['posture'][-1])*self.assym_duration(duration_s_min)

        for posture in posture_data_LBX:
            # Compute duration_s_min
            duration_s_min = posture['time'] * 60 / duration

            score_B = score_B + int(posture['posture'][-1])*self.assym_duration(duration_s_min)
            
        # Add the total posture score to the cumulative total score
        self.postures_score += score_A + score_B
        
    def assym_duration(self, duration_s):
        
        if(duration_s >= 4):
            return 1.5
        elif(duration_s >= 10):
            return 2.5
        elif(duration_s >= 13):
            return 3
        
        return 0
    
    def far_reach_duration(self, duration_s):
        
        if(duration_s >= 4):
            return 1
        elif(duration_s >= 10):
            return 1.5
        elif(duration_s >= 13):
            return 2
        
        return 0

    def calculate_score_A(self, posture_type, duration_s_min):
        score_A = 0
        # Calculate score A based on posture type and duration_s_min
        if posture_type == 1:
            score_A = self.calculate_score_A_type_1(duration_s_min)
        elif posture_type == 2:
            score_A = self.calculate_score_A_type_2(duration_s_min)
        elif posture_type == 3:
            score_A = self.calculate_score_A_type_3(duration_s_min)
        elif posture_type == 4:
            score_A = self.calculate_score_A_type_4(duration_s_min)
        elif posture_type == 5:
            score_A = self.calculate_score_A_type_5(duration_s_min)
        elif posture_type == 6:
            score_A = self.calculate_score_A_type_6(duration_s_min)
        elif posture_type == 7:
            score_A = self.calculate_score_A_type_7(duration_s_min)
        elif posture_type == 8:
            score_A = self.calculate_score_A_type_8(duration_s_min)
        elif posture_type == 9:
            score_A = self.calculate_score_A_type_9(duration_s_min)
        elif posture_type == 10:
            score_A = self.calculate_score_A_type_10(duration_s_min)
        elif posture_type == 11:
            score_A = self.calculate_score_A_type_11(duration_s_min)
        elif posture_type == 12:
            score_A = self.calculate_score_A_type_12(duration_s_min)
        elif posture_type == 13:
            score_A = self.calculate_score_A_type_13(duration_s_min)
        elif posture_type == 14:
            score_A = self.calculate_score_A_type_14(duration_s_min)
        elif posture_type == 15:
            score_A = self.calculate_score_A_type_15(duration_s_min)
        elif posture_type == 16:
            score_A = self.calculate_score_A_type_16(duration_s_min)

        return score_A

    def calculate_score_A_type_1(self, duration_s_min):
        if duration_s_min < 12:
            return 0
        elif 12 <= duration_s_min < 16:
            return 0.5
        elif 16 <= duration_s_min < 20:
            return 1
        elif 20 <= duration_s_min < 30:
            return 1
        elif 30 <= duration_s_min < 40:
            return 1
        elif 40 <= duration_s_min < 50:
            return 1.5
        else:
            return 2

    def calculate_score_A_type_2(self, duration_s_min):
        if duration_s_min < 3:
            return 0
        elif 3 <= duration_s_min < 4.5:
            return 0.7
        elif 4.5 <= duration_s_min < 6:
            return 1
        elif 6 <= duration_s_min < 9:
            return 1.5
        elif 9 <= duration_s_min < 12:
            return 2
        elif 12 <= duration_s_min < 16:
            return 3
        elif 16 <= duration_s_min < 20:
            return 4
        elif 20 <= duration_s_min < 30:
            return 6
        elif 30 <= duration_s_min < 40:
            return 8
        elif 40 <= duration_s_min < 50:
            return 11
        else:
            return 13

    def calculate_score_A_type_3(self, duration_s_min):
        if duration_s_min < 3:
            return 0
        elif 3 <= duration_s_min < 4.5:
            return 2
        elif 4.5 <= duration_s_min < 6:
            return 3
        elif 6 <= duration_s_min < 9:
            return 5
        elif 9 <= duration_s_min < 12:
            return 7
        elif 12 <= duration_s_min < 16:
            return 9.5
        elif 16 <= duration_s_min < 20:
            return 12
        elif 20 <= duration_s_min < 30:
            return 18
        elif 30 <= duration_s_min < 40:
            return 23
        elif 40 <= duration_s_min < 50:
            return 32
        else:
            return 40
        
    def calculate_score_A_type_4(self, duration_s_min):
        if duration_s_min < 3:
            return 0
        elif 3 <= duration_s_min < 4.5:
            return 3.3
        elif 4.5 <= duration_s_min < 6:
            return 5
        elif 6 <= duration_s_min < 9:
            return 8.5
        elif 9 <= duration_s_min < 12:
            return 12
        elif 12 <= duration_s_min < 16:
            return 17
        elif 16 <= duration_s_min < 20:
            return 21
        elif 20 <= duration_s_min < 30:
            return 30
        elif 30 <= duration_s_min < 40:
            return 38
        elif 40 <= duration_s_min < 50:
            return 51
        else:
            return 63

    def calculate_score_A_type_5(self, duration_s_min):
        if duration_s_min < 3:
            return 0
        elif 3 <= duration_s_min < 4.5:
            return 3.3
        elif 4.5 <= duration_s_min < 6:
            return 5
        elif 6 <= duration_s_min < 9:
            return 8.5
        elif 9 <= duration_s_min < 12:
            return 12
        elif 12 <= duration_s_min < 16:
            return 17
        elif 16 <= duration_s_min < 20:
            return 21
        elif 20 <= duration_s_min < 30:
            return 30
        elif 30 <= duration_s_min < 40:
            return 38
        elif 40 <= duration_s_min < 50:
            return 51
        else:
            return 63

    def calculate_score_A_type_6(self, duration_s_min):
        if duration_s_min < 3:
            return 0
        elif 3 <= duration_s_min < 4.5:
            return 5.3
        elif 4.5 <= duration_s_min < 6:
            return 8
        elif 6 <= duration_s_min < 9:
            return 14
        elif 9 <= duration_s_min < 12:
            return 19
        elif 12 <= duration_s_min < 16:
            return 26
        elif 16 <= duration_s_min < 20:
            return 33
        elif 20 <= duration_s_min < 30:
            return 47
        elif 30 <= duration_s_min < 40:
            return 60
        elif 40 <= duration_s_min < 50:
            return 80
        else:
            return 100

    def calculate_score_A_type_7(self, duration_s_min):
        if duration_s_min < 20:
            return 0
        elif 20 <= duration_s_min < 30:
            return 0.5
        elif 30 <= duration_s_min < 40:
            return 1
        elif 40 <= duration_s_min < 50:
            return 1.5
        elif duration_s_min >= 50:
            return 2

    def calculate_score_A_type_8(self, duration_s_min):
        if duration_s_min < 6:
            return 0
        elif 6 <= duration_s_min < 9:
            return 0.5
        elif 9 <= duration_s_min < 12:
            return 1
        elif 12 <= duration_s_min < 16:
            return 1.5
        elif 16 <= duration_s_min < 20:
            return 2
        elif 20 <= duration_s_min < 30:
            return 3
        elif 30 <= duration_s_min < 40:
            return 4
        elif 40 <= duration_s_min < 50:
            return 5.5
        elif duration_s_min >= 50:
            return 7
        
    # Score A calculations for each posture type
    def calculate_score_A_type_9(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 0.7
        elif 4.5 <= duration_s_min < 6:
            score_A = 1
        elif 6 <= duration_s_min < 9:
            score_A = 1.5
        elif 9 <= duration_s_min < 12:
            score_A = 2
        elif 12 <= duration_s_min < 16:
            score_A = 3
        elif 16 <= duration_s_min < 20:
            score_A = 4
        elif 20 <= duration_s_min < 30:
            score_A = 6
        elif 30 <= duration_s_min < 40:
            score_A = 8
        elif 40 <= duration_s_min < 50:
            score_A = 11
        else:
            score_A = 13
        return score_A

    # Score A calculations for each posture type
    def calculate_score_A_type_10(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 2.7
        elif 4.5 <= duration_s_min < 6:
            score_A = 4
        elif 6 <= duration_s_min < 9:
            score_A = 7
        elif 9 <= duration_s_min < 12:
            score_A = 10
        elif 12 <= duration_s_min < 16:
            score_A = 13
        elif 16 <= duration_s_min < 20:
            score_A = 16
        elif 20 <= duration_s_min < 30:
            score_A = 23
        elif 30 <= duration_s_min < 40:
            score_A = 30
        elif 40 <= duration_s_min < 50:
            score_A = 40
        else:
            score_A = 50
        return score_A

    # Score A calculations for each posture type
    def calculate_score_A_type_11(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 4
        elif 4.5 <= duration_s_min < 6:
            score_A = 6
        elif 6 <= duration_s_min < 9:
            score_A = 10
        elif 9 <= duration_s_min < 12:
            score_A = 14
        elif 12 <= duration_s_min < 16:
            score_A = 20
        elif 16 <= duration_s_min < 20:
            score_A = 25
        elif 20 <= duration_s_min < 30:
            score_A = 35
        elif 30 <= duration_s_min < 40:
            score_A = 45
        elif 40 <= duration_s_min < 50:
            score_A = 60
        else:
            score_A = 75
        return score_A

    # Score A calculations for each posture type
    def calculate_score_A_type_12(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 3.3
        elif 4.5 <= duration_s_min < 6:
            score_A = 5
        elif 6 <= duration_s_min < 9:
            score_A = 7
        elif 9 <= duration_s_min < 12:
            score_A = 9
        elif 12 <= duration_s_min < 16:
            score_A = 12
        elif 16 <= duration_s_min < 20:
            score_A = 15
        elif 20 <= duration_s_min < 30:
            score_A = 21
        elif 30 <= duration_s_min < 40:
            score_A = 27
        elif 40 <= duration_s_min < 50:
            score_A = 36
        else:
            score_A = 45
        return score_A

    # Score A calculations for each posture type
    def calculate_score_A_type_13(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 4
        elif 4.5 <= duration_s_min < 6:
            score_A = 6
        elif 6 <= duration_s_min < 9:
            score_A = 10
        elif 9 <= duration_s_min < 12:
            score_A = 14
        elif 12 <= duration_s_min < 16:
            score_A = 20
        elif 16 <= duration_s_min < 20:
            score_A = 25
        elif 20 <= duration_s_min < 30:
            score_A = 35
        elif 30 <= duration_s_min < 40:
            score_A = 45
        elif 40 <= duration_s_min < 50:
            score_A = 60
        else:
            score_A = 75
        return score_A

    # Score A calculations for each posture type
    def calculate_score_A_type_14(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 3.3
        elif 4.5 <= duration_s_min < 6:
            score_A = 5
        elif 6 <= duration_s_min < 9:
            score_A = 8.5
        elif 9 <= duration_s_min < 12:
            score_A = 12
        elif 12 <= duration_s_min < 16:
            score_A = 17
        elif 16 <= duration_s_min < 20:
            score_A = 21
        elif 20 <= duration_s_min < 30:
            score_A = 30
        elif 30 <= duration_s_min < 40:
            score_A = 38
        elif 40 <= duration_s_min < 50:
            score_A = 51
        else:
            score_A = 63
        return score_A

    # Score A calculations for each posture type
    def calculate_score_A_type_15(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 6
        elif 4.5 <= duration_s_min < 6:
            score_A = 9
        elif 6 <= duration_s_min < 9:
            score_A = 15
        elif 9 <= duration_s_min < 12:
            score_A = 21
        elif 12 <= duration_s_min < 16:
            score_A = 29
        elif 16 <= duration_s_min < 20:
            score_A = 37
        elif 20 <= duration_s_min < 30:
            score_A = 53
        elif 30 <= duration_s_min < 40:
            score_A = 68
        elif 40 <= duration_s_min < 50:
            score_A = 91
        else:
            score_A = 113
        return score_A

    # Score A calculations for each posture type
    def calculate_score_A_type_16(self, duration_s_min):
        if duration_s_min < 3:
            score_A = 0
        elif 3 <= duration_s_min < 4.5:
            score_A = 6.7
        elif 4.5 <= duration_s_min < 6:
            score_A = 10
        elif 6 <= duration_s_min < 9:
            score_A = 22
        elif 9 <= duration_s_min < 12:
            score_A = 33
        elif 12 <= duration_s_min < 16:
            score_A = 50
        else:
            score_A = 66
        return score_A


    def calculate_forces(self):
        # Placeholder for calculating forces score
        pass

    def calculate_loads(self, loads, index=None):
        self.loads_score = 0
        
        #Find end index of loads based on that of posture
        loads = self.loads
        load_index = None
        if index is not None:
            end_time = self.postures[index-1]["timestamp"]
            for i in range(len(loads)):
                if loads[i]["time"] >= end_time:
                    load_index = i
                    break
        
        # Iterate over the load data
        index_counter = 0
        for load in loads:
            # Check if the entry time exceeds the duration (if provided)
            if(load_index is not None):
                if index_counter > load_index:
                    break
            index_counter += 1

            load_type = load["type"]
            transport_type = load["transport"]
            weight = load["weight"]
            posture = load["posture"]
            conditions = load["conditions"]     #no idea how to get this (user input i guess)
            frequency = load["frequency"]
            duration = load["duration"]
            distance = load["distance"]
            
            #Initialize component scores
            load_points = 0
            posture_points = 0
            condition_points = 0
            duration_factor = 0
            
            if load_type == "repositioning":
                #weight score
                if self.operator_gender == "M":
                    if 3 <= weight < 10:
                        load_points = 1
                    elif 10 <= weight < 15:
                        load_points = 1.5
                    elif 15 <= weight < 20:
                        load_points = 2
                    elif 20 <= weight < 25:
                        load_points = 3
                    elif 25 <= weight < 30:
                        load_points = 4
                    elif 30 <= weight < 35:
                        load_points = 10
                    elif 35 <= weight < 40:
                        load_points = 17
                    elif weight >= 40:
                        load_points = 25
                else:
                    if 2 <= weight < 5:
                        load_points = 1
                    elif 5 <= weight < 7:
                        load_points = 1.5
                    elif 7 <= weight < 10:
                        load_points = 2
                    elif 10 <= weight < 12:
                        load_points = 3
                    elif 12 <= weight < 15:
                        load_points = 4
                    elif 15 <= weight < 20:
                        load_points = 5.5
                    elif 20 <= weight < 25:
                        load_points = 7
                    elif weight >= 25:
                        load_points = 25
                
                #posture score assumed to be equal to load["posture"]
                posture_points = posture
                #condition score assumed to be equal to load["conditions"]
                condition_points = conditions
                
                #frequency/duration/distance factor
                if 5 <= frequency < 25:
                    duration_factor = 1
                elif 25 <= frequency < 120:
                    duration_factor = 2
                elif 120 <= frequency < 350:
                    duration_factor = 4
                elif 350 <= frequency < 750:
                    duration_factor = 6
                elif 750 <= frequency < 1000:
                    duration_factor = 8
                elif 1000 <= frequency < 1500:
                    duration_factor = 10
                elif 1500 <= frequency < 2000:
                    duration_factor = 11
                elif 2000 <= frequency < 2500:
                    duration_factor = 13
                elif 2500 <= frequency < 3000:
                    duration_factor = 14
                elif frequency >= 3000:
                    duration_factor = 15

            elif load_type == "carrying":
                #weight score
                if self.operator_gender == "M":
                    if 3 <= weight < 10:
                        load_points = 1
                    elif 10 <= weight < 15:
                        load_points = 1.5
                    elif 15 <= weight < 20:
                        load_points = 2
                    elif 20 <= weight < 25:
                        load_points = 3
                    elif 25 <= weight < 30:
                        load_points = 4
                    elif 30 <= weight < 35:
                        load_points = 10
                    elif 35 <= weight < 40:
                        load_points = 17
                    elif weight >= 40:
                        load_points = 25
                else:
                    if 2 <= weight < 5:
                        load_points = 1
                    elif 5 <= weight < 7:
                        load_points = 1.5
                    elif 7 <= weight < 10:
                        load_points = 2
                    elif 10 <= weight < 12:
                        load_points = 3
                    elif 12 <= weight < 15:
                        load_points = 4
                    elif 15 <= weight < 20:
                        load_points = 5.5
                    elif 20 <= weight < 25:
                        load_points = 7
                    elif weight >= 25:
                        load_points = 25
                
                #posture score assumed to be given by load["posture"]
                posture_points = posture
                #condition score assumed to be given by load["conditions"]
                condition_points = conditions
                
                #frequency/duration/distance factor
                if 300 <= distance < 650:
                    duration_factor = 1
                elif 650 <= distance < 2500:
                    duration_factor = 2
                elif 2500 <= distance < 6000:
                    duration_factor = 4
                elif 6000 <= distance < 12000:
                    duration_factor = 6
                elif 12000 <= distance < 16000:
                    duration_factor = 8
                elif distance >= 16000:
                    duration_factor = 10
                    
            elif load_type == "holding":
                #weight score
                if self.operator_gender == "M":
                    if 3 <= weight < 10:
                        load_points = 1
                    elif 10 <= weight < 15:
                        load_points = 1.5
                    elif 15 <= weight < 20:
                        load_points = 2
                    elif 20 <= weight < 25:
                        load_points = 3
                    elif 25 <= weight < 30:
                        load_points = 4
                    elif 30 <= weight < 35:
                        load_points = 10
                    elif 35 <= weight < 40:
                        load_points = 17
                    elif weight >= 40:
                        load_points = 25
                else:
                    if 2 <= weight < 5:
                        load_points = 1
                    elif 5 <= weight < 7:
                        load_points = 1.5
                    elif 7 <= weight < 10:
                        load_points = 2
                    elif 10 <= weight < 12:
                        load_points = 3
                    elif 12 <= weight < 15:
                        load_points = 4
                    elif 15 <= weight < 20:
                        load_points = 5.5
                    elif 20 <= weight < 25:
                        load_points = 7
                    elif weight >= 25:
                        load_points = 25
                
                #posture score assumed to be given by load["posture"]
                posture_points = posture
                #condition score assumed to be given by load["conditions"]
                condition_points = conditions
                
                #frequency/duration/distance factor
                if 2.5 <= duration < 10:
                    duration_factor = 1
                elif 10 <= duration < 37:
                    duration_factor = 2
                elif 37 <= duration < 90:
                    duration_factor = 4
                elif 90 <= duration < 180:
                    duration_factor = 6
                elif 180 <= duration < 240:
                    duration_factor = 8
                elif duration >= 240:
                    duration_factor = 10
                    
            elif load_type == "push_pull_short":
                #weight score
                if self.operator_gender == "M":
                    if transport_type == "wheelbarrow":
                        if 50 <= weight < 75:
                            load_points = 0.5
                        elif 75 <= weight < 100:
                            load_points = 1
                        elif 100 <= weight < 150:
                            load_points = 1.5
                        elif 150 <= weight < 200:
                            load_points = 2
                        elif 200 <= weight < 250:
                            load_points = 3
                        elif weight >= 250:
                            load_points = 4
                    elif transport_type == "carriage":
                        if 50 <= weight < 75:
                            load_points = 0.5
                        elif 75 <= weight < 100:
                            load_points = 1
                        elif 100 <= weight < 150:
                            load_points = 1.5
                        elif 150 <= weight < 250:
                            load_points = 2
                        elif 250 <= weight < 350:
                            load_points = 3
                        elif 350 <= weight < 550:
                            load_points = 4
                        elif weight >= 550:
                            load_points = 5
                    elif transport_type == "cart":
                        if 50 <= weight < 75:
                            load_points = 0.5
                        elif 75 <= weight < 150:
                            load_points = 1
                        elif 150 <= weight < 250:
                            load_points = 1.5
                        elif 250 <= weight < 350:
                            load_points = 2
                        elif 350 <= weight < 500:
                            load_points = 3
                        elif 500 <= weight < 600:
                            load_points = 4
                        elif 600 <= weight < 800:
                            load_points = 5
                        elif 800 <= weight < 1250:
                            load_points = 6
                        elif weight >= 1250:
                            load_points = 8
                else:
                    if transport_type == "wheelbarrow":
                        if 40 <= weight < 60:
                            load_points = 0.5
                        elif 60 <= weight < 80:
                            load_points = 1
                        elif 80 <= weight < 115:
                            load_points = 1.5
                        elif 115 <= weight < 155:
                            load_points = 2
                        elif 155 <= weight < 195:
                            load_points = 3
                        elif weight >= 195:
                            load_points = 4
                    elif transport_type == "carriage":
                        if 40 <= weight < 60:
                            load_points = 0.5
                        elif 60 <= weight < 80:
                            load_points = 1
                        elif 80 <= weight < 115:
                            load_points = 1.5
                        elif 115 <= weight < 195:
                            load_points = 2
                        elif 195 <= weight < 270:
                            load_points = 3
                        elif 270 <= weight < 425:
                            load_points = 4
                        elif weight >= 425:
                            load_points = 5
                    elif transport_type == "cart":
                        if 40 <= weight < 60:
                            load_points = 0.5
                        elif 60 <= weight < 115:
                            load_points = 1
                        elif 115 <= weight < 195:
                            load_points = 1.5
                        elif 195 <= weight < 270:
                            load_points = 2
                        elif 270 <= weight < 385:
                            load_points = 3
                        elif 385 <= weight < 460:
                            load_points = 4
                        elif 460 <= weight < 615:
                            load_points = 5
                        elif 615 <= weight < 960:
                            load_points = 6
                        elif weight >= 960:
                            load_points = 8
                
                #posture score assumed to be equal to load["posture"]
                posture_points = posture
                #condition score assumed to be equal to load["conditions"]
                condition_points = conditions
                
                #frequency/duration/distance factor
                if 5 <= frequency < 25:
                    duration_factor = 1
                elif 25 <= frequency < 120:
                    duration_factor = 2
                elif 120 <= frequency < 350:
                    duration_factor = 4
                elif 350 <= frequency < 750:
                    duration_factor = 6
                elif 750 <= frequency < 1000:
                    duration_factor = 8
                elif 1000 <= frequency < 1500:
                    duration_factor = 10
                elif 1500 <= frequency < 2000:
                    duration_factor = 11
                elif 2000 <= frequency < 2500:
                    duration_factor = 13
                elif 2500 <= frequency < 3000:
                    duration_factor = 14
                elif frequency >= 3000:
                    duration_factor = 15
                    
            elif load_type == "push_pull_long":
                #weight score
                if self.operator_gender == "M":
                    if transport_type == "wheelbarrow":
                        if 50 <= weight < 75:
                            load_points = 0.5
                        elif 75 <= weight < 100:
                            load_points = 1
                        elif 100 <= weight < 150:
                            load_points = 1.5
                        elif 150 <= weight < 200:
                            load_points = 2
                        elif 200 <= weight < 250:
                            load_points = 3
                        elif weight >= 250:
                            load_points = 4
                    elif transport_type == "carriage":
                        if 50 <= weight < 75:
                            load_points = 0.5
                        elif 75 <= weight < 100:
                            load_points = 1
                        elif 100 <= weight < 150:
                            load_points = 1.5
                        elif 150 <= weight < 250:
                            load_points = 2
                        elif 250 <= weight < 350:
                            load_points = 3
                        elif 350 <= weight < 550:
                            load_points = 4
                        elif weight >= 550:
                            load_points = 5
                    elif transport_type == "cart":
                        if 50 <= weight < 75:
                            load_points = 0.5
                        elif 75 <= weight < 150:
                            load_points = 1
                        elif 150 <= weight < 250:
                            load_points = 1.5
                        elif 250 <= weight < 350:
                            load_points = 2
                        elif 350 <= weight < 500:
                            load_points = 3
                        elif 500 <= weight < 600:
                            load_points = 4
                        elif 600 <= weight < 800:
                            load_points = 5
                        elif 800 <= weight < 1250:
                            load_points = 6
                        elif weight >= 1250:
                            load_points = 8
                else:
                    if transport_type == "wheelbarrow":
                        if 40 <= weight < 60:
                            load_points = 0.5
                        elif 60 <= weight < 80:
                            load_points = 1
                        elif 80 <= weight < 115:
                            load_points = 1.5
                        elif 115 <= weight < 155:
                            load_points = 2
                        elif 155 <= weight < 195:
                            load_points = 3
                        elif weight >= 195:
                            load_points = 4
                    elif transport_type == "carriage":
                        if 40 <= weight < 60:
                            load_points = 0.5
                        elif 60 <= weight < 80:
                            load_points = 1
                        elif 80 <= weight < 115:
                            load_points = 1.5
                        elif 115 <= weight < 195:
                            load_points = 2
                        elif 195 <= weight < 270:
                            load_points = 3
                        elif 270 <= weight < 425:
                            load_points = 4
                        elif weight >= 425:
                            load_points = 5
                    elif transport_type == "cart":
                        if 40 <= weight < 60:
                            load_points = 0.5
                        elif 60 <= weight < 115:
                            load_points = 1
                        elif 115 <= weight < 195:
                            load_points = 1.5
                        elif 195 <= weight < 270:
                            load_points = 2
                        elif 270 <= weight < 385:
                            load_points = 3
                        elif 385 <= weight < 460:
                            load_points = 4
                        elif 460 <= weight < 615:
                            load_points = 5
                        elif 615 <= weight < 960:
                            load_points = 6
                        elif weight >= 960:
                            load_points = 8
            
                #posture score assumed to be given by load["posture"]
                posture_points = posture
                #condition score assumed to be given by load["conditions"]
                condition_points = conditions
                
                #frequency/duration/distance factor
                if 300 <= distance < 650:
                    duration_factor = 1
                elif 650 <= distance < 2500:
                    duration_factor = 2
                elif 2500 <= distance < 6000:
                    duration_factor = 4
                elif 6000 <= distance < 12000:
                    duration_factor = 6
                elif 12000 <= distance < 16000:
                    duration_factor = 8
                elif distance >= 16000:
                    duration_factor = 10
            
            if (self.operator_gender == "M" and weight >= 3) or (self.operator_gender == "F" and weight >= 2):     #weights less than 3 kg (or 2 kg for female) are not considered in the EAWS
                self.loads_score += (load_points + posture_points + condition_points)*duration_factor


    def calculate_upper_limbs(self):
        # Placeholder for calculating upper limbs score
        pass

    def calculate_eaws_score(self):
        # Calculate the EAWS score as the sum of all sub-scores
        eaws_score = self.whole_body_extra_points + self.postures_score + self.forces_score + self.loads_score + self.upper_limbs_score
        return eaws_score

    def calculate_intermediate_eaws_score(self, intermediate_time, index):
            # Calculate posture score up to the intermediate time
            self.calculate_posture_score(intermediate_time, index)
            
            # Calculate the EAWS score as the sum of posture score and other sub-scores
            eaws_score = self.whole_body_extra_points + self.postures_score + self.forces_score + self.loads_score + self.upper_limbs_score
            
            return self.whole_body_extra_points, self.postures_score, self.loads_score, eaws_score