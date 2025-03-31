# pylint: skip-file

"""
The aim of this toolbox is to have certain functions that are not very long, but are essential and very usefull when it comes to
executing the main code.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 26/04/2023
"""

import math
from datetime import datetime  # This allows to work with the correct time format

import pandas as pd  # Library for data manipulation

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# -----------------------------------------BEGINNING FUNCTION USE_TIME----------------------------------------------------
# This function provides the user with the time and the intensity of the rain between the starting and the ending dates:
# this list may have jumps in time. The same is done for the observations, which might also have jumps.
# This is why the function also provides a full time list following the desired time step.


def USE_PERIOD(
    rain_file,
    rain_time_col_name,
    rain_intensity_col_name,
    observations_file,
    obs_time_col_name,
    obs_flow_col_name,
    obs_weir_col_name,
    starting_date,
    ending_date,
    dt,
):
    starting_date = datetime.strptime(starting_date, "%Y-%m-%d %H:%M:%S")  # Conversion to datetime.datetime
    ending_date = datetime.strptime(ending_date, "%Y-%m-%d %H:%M:%S")  # Conversion to datetime.datetime

    # ---------------------------------------FULL_STUDY_PERIOD---------------------------------------

    full_study_period = []  # Initialization of a list to store the full time list during the study period

    # Generates the full time list from the beginning to the ending following the time step
    dt = str(dt) + "min"
    full_study_period = pd.date_range(start=starting_date, end=ending_date, freq=dt)

    # ---------------------------------------------RAIN---------------------------------------------

    # Selects the data from the rain file
    rain = pd.read_csv(rain_file, delimiter=";")  # This reads the rain file
    rain_date = rain[rain_time_col_name].values  # Takes the values of the column called 'Date TU'
    rain_intensity = rain[rain_intensity_col_name].values  # Takes the values of the column called 'mm/min'

    for i in range(len(rain_date)):
        rain_date[i] = datetime.strptime(rain_date[i], "%d/%m/%Y %H:%M")  # Conversion to datetime.datetime

    rain_time = []  # Initialization of a list to store the studied period of time in the rain file
    intensity_period = []  # Initialization of a list to store the rain intensity associated to the rain_time

    # Taking only the time and the intensity during the study period
    for i in range(len(rain_date)):
        if starting_date <= rain_date[i] and ending_date >= rain_date[i]:
            intensity_period.append(rain_intensity[i])  # Considers the intensities only during the study period
            rain_time.append(rain_date[i])  # Considers the rain time only during the study period

    # ---------------------------------------------OBSERVATIONS---------------------------------------------

    # Selects the data from the observation file
    observations = pd.read_csv(observations_file, delimiter=";", low_memory=False)  # This reads the observations file
    observations_date = observations[obs_time_col_name].values  # Takes the values of the column called 'Date'
    observations_flow = observations[obs_flow_col_name].values  # Takes the values of the column called 'Debit [m3/s]'
    observations_weir = observations[
        obs_weir_col_name
    ].values  # Takes the values of the column called 'Debit dev [m3/s]'

    for i in range(len(observations_date)):
        observations_date[i] = datetime.strptime(
            observations_date[i], "%d/%m/%Y %H:%M"
        )  # Conversion to datetime.datetime

    obs_time = []  # Initialization of a list to store the studied period of time in the observations file
    obs_flow = (
        []
    )  # Initialization of a list to store the observed flow associated to each time step in the studied period
    obs_weir = []

    # Taking only the time and the intensity during the study period
    for i in range(len(observations_date)):
        if starting_date <= observations_date[i] and ending_date >= observations_date[i]:
            obs_time.append(observations_date[i])  # Considers the observations time only during the study period
            obs_flow.append(observations_flow[i])  # Considers the observed flow only during the study period
            obs_weir.append(observations_weir[i])  # Considers the observed weir only during the study period

    return rain_time, intensity_period, obs_time, obs_flow, obs_weir, full_study_period


# -----------------------------------------ENDING FUNCTION USE_TIME-----------------------------------------------------

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


# --------------------------------BEGINNING FUNCTION REMOVE_INITIAL_LOSSES----------------------------------------------
# This function provides the user with the effective intensity of the rain. It removes the initial losses.
def REMOVE_INITIAL_LOSSES(temporary_intensity_list, IL):
    effective_intensity_list = []  # This list will be filled with the effective intensity
    losses = 0  # This cummulates the losses before reaching the IL. It starts in cero since nothing has been lost yet.

    for i in range(len(temporary_intensity_list)):
        if IL == losses:
            effective_intensity_list.append(
                temporary_intensity_list[i]
            )  # Once the losses equal the IL, the effective intensity equals the original intensity

        if losses < IL:
            if (losses + temporary_intensity_list[i]) <= IL:  # This checks if the losses reach the IL yet.
                losses += temporary_intensity_list[i]  # This accumulates the losses
                effective_intensity_list.append(
                    0
                )  # Since all rain has been lost until this point, the effective intensity is cero.
            else:
                effective_intensity_list.append(
                    temporary_intensity_list[i] - (IL - losses)
                )  # This is the effective intensity right before losses reach IL.
                losses = IL  # The losses have reached the IL
    return effective_intensity_list


# --------------------------------ENDING FUNCTION REMOVE_INITIAL_LOSSES----------------------------------------------

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


# -----------------------------BEGINNING FUNCTION RATIONAL_METHOD--------------------------------------------
# This function provides the user with the flow generated by the effective intensity before going through the reservoir.
# This works only with individual values. Take it into account when using it.
def RATIONAL_METHOD(effective_intensity_point, surface, RC):
    # The values found in the effective_intensity_list are in units of mm/min.
    flow = (
        effective_intensity_point * surface * RC * (1 / 6)
    )  # The value of 1/6 is the conversion factor. Surface is in ha and effective_intensity_point in mm/min. Result in m3/s.

    return flow


# -------------------------------ENDING FUNCTION RATIONAL_METHOD---------------------------------------------

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


# ----------------------------------BEGINNING FUNCTION COMPLETE STUDY PERIOD------------------------------------------------
# This function provides a flow list that is evenly paced according to the selected time step.
# It considers that there can be a constant base to be added at every moment. (value)
def COMPLETE_STUDY_PERIOD(time, full_study_period, flow, value):
    flow_study_period = [value] * len(
        full_study_period
    )  # This list will be filled with the 'value' during the full_study_period

    if type(value) == int or type(value) == float:
        for i in range(len(full_study_period)):
            for j in range(len(time)):
                if full_study_period[i] == time[j]:
                    flow_study_period[i] = flow_study_period[i] + flow[j]
    else:
        for i in range(len(full_study_period)):
            for j in range(len(time)):
                if full_study_period[i] == time[j]:
                    flow_study_period[i] = flow[j]

    return flow_study_period


# ----------------------------------ENDING FUNCTION COMPLETE STUDY PERIOD------------------------------------------------

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


# -----------------------------------BEGINNING FUNCTION LINEAR RESERVOIR------------------------------------------------
# This function takes an upstream flow and transports it through a pipe. The result is the downstream flow.
def LINEAR_RESERVOIR(decision, K, length_pipe, catchment_surface, p_imp_surface, slope_pipe, dt, Q_up):
    if decision == "yes":
        K = K  # There is a lag time.

    else:
        K = (
            0.50
            * (catchment_surface ** (-0.0076))
            * (p_imp_surface ** (-0.512))
            * (slope_pipe ** (-0.401))
            * length_pipe ** (0.608)
        )
        # The lag time is created with the Desbordes Formula.

    # The C1 and C2 coefficients of the linear reservoir method are generated.
    C1 = math.exp((-dt) / K)  # K and dt MUST be in minutes.
    C2 = 1 - C1

    Q_down = [0 for i in range(len(Q_up))]  # The Q_down list is filled with 0 in all the time length.
    Q_down[0] = Q_up[0]  # This is the initial condition for the linear reservoir method. Main hypothesis.

    # The linear reservoir method is executed.
    for i in range(len(Q_up) - 1):
        Q_down[i + 1] = C1 * Q_down[i] + C2 * Q_up[i + 1]

    return Q_down


# -----------------------------------ENDING FUNCTION LINEAR RESERVOIR------------------------------------------------

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# --------------------------------------BEGINNING FUNCTION OVERFLOW--------------------------------------------------

# This function aims to see if there is an overflow in the system. The function assumes the presence of a threshold law.


def OVERFLOW(law, Q_down, full_study_period, Q_lim, threshold_law):
    spill_dates = []
    Q_weir = [0 for i in range(len(full_study_period))]

    # If there is a threshold law, then we apply it.
    if law == "yes":
        # At this point we will define the full list of overflows at every moment of the full study period.
        spill_dates_list = []
        for i in range(len(Q_down)):
            Q = Q_down[i]

            if Q >= Q_lim:
                Q_weir[i] = eval(threshold_law)  # The equation is written in terms of Q.

                # If there is an overflow, we store the date
                spill_dates_list.append(full_study_period[i])

        # The dates cannot be counted more than once.
        spill_dates.append(spill_dates_list[0])
        for i in range(1, len(spill_dates_list)):
            if spill_dates_list[i].day != spill_dates_list[i - 1].day:
                spill_dates.append(spill_dates_list[i])

        # We count the number of days with spill. No matter the amount of spills per day, it is counted as only one.
        num_spills = len(spill_dates)

    # If there is NO threshold law, the geometry is asked.
    if law == "no":
        Q_weir = "Geometry needed to evaluate if there is or if there is no overflow"
        spill_dates = "Geometry needed to evaluate the overflow dates"
        num_spills = "Geometry needed to evaluate the number of overflow"

    return Q_weir, spill_dates, num_spills


# ----------------------------------------ENDING FUNCTION OVERFLOW--------------------------------------------------
