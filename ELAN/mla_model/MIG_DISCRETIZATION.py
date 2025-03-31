# pylint: skip-file

"""
This code produces the flow at the end of a catchment and the overflow when the maximum capacity is reached.
It analizes a catchment as a whole and its division in subwatersheds, as far as the user has all the necessary information from every one
of the parts of the system (every subwatershed and the pipes connecting them). It is highly advised to have a map with the watersheds and pipes drawn and labeled.
It also stocks many important variables that the user can make use of, such as the effective ìntensity of the rain, the number of rains, among others.

All the code is written in english.

This code is a second version from the one created by the PhD student Violeta Montoya Coronado in the DEEP Laboratory from INSA Lyon.
This work is done under the TONIC project and as part of the End-of-studies internship for Civil Engineering and Urbanism.

As a suggestion, this code should be read carefully and slowly to be well understood.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 03/05/2023
"""

import csv
from itertools import zip_longest
from pathlib import Path

import matplotlib.pyplot as plt

from . import MIG_TOOLBOX, MIG_TRANSFERED_FLOW, MIG_UPSTREAM_FLOW


def mla_main_run(
    rain, wastewater, observation, path_csv, Q_lim, threshold_law, period, time_between_rains_runoff, watersheds, pipes
):
    # Rain file
    rain_file = rain.rain_file
    rain_time_col_name = rain.rain_time_col_name
    rain_intensity_col_name = rain.rain_intensity_col_name

    # Wastewater pattern file
    wastewater_pattern = wastewater.wastewater_pattern
    ww_time_col_name = wastewater.ww_time_col_name
    ww_flow_col_name = wastewater.ww_flow_col_name

    # Observation file
    observations_file = observation.observations_file
    obs_time_col_name = observation.obs_time_col_name
    obs_flow_col_name = observation.obs_flow_col_name
    obs_weir_col_name = observation.obs_weir_col_name

    # Watersheds data
    catchment_surface = watersheds.catchment_surface
    p_imp_surface = watersheds.p_imp_surface
    p_des_surface = [0] * len(p_imp_surface)
    hab = watersheds.hab
    PE = watersheds.pop_eq
    PII = watersheds.pii
    FRII = watersheds.frii
    KRII = watersheds.krii
    FIMP = watersheds.fimp
    FPER = watersheds.fper
    IL = watersheds.initial_losses
    Hinf = watersheds.hinf
    Hsoil = watersheds.hsoil

    # Pipes data
    pipe_order = watersheds.pipe_order
    slope_pipe = pipes.slope
    length_pipe = pipes.length
    K = pipes.lag_surface_runoff
    decision = pipes.decision

    ####  Rajout des input dans MIG_DISCRETIZATION le temps de réfléchir sur la syntaxe et de corriger les beugs primaires.

    # Step 3: Choose study period and the desired time step
    # Pay close attention to the format: yyyy-mm-dd hh:mm:ss
    starting_date = period.starting_date
    ending_date = period.ending_date  # "2008-06-11 23:59:00"  # Pay close attention to the format: yyyy-mm-dd hh:mm:ss

    # = 1  # This is the time step at which the code will run everything. It is adviced to use the timestep from the rain record.[min]
    time_step = period.time_step

    # Step 4: Enter the information of the territory. This step must be done very carefully.

    # ......---------------------------------------------CATCHMENTS---------------------------------------------......
    # All the characteristics are vectors of the size of number of catchments that are being analyzed.
    # In this case, the first value of every vector belongs to the total catchment, the rest are from the sub-catchments that are part of it.

    # Time between rains for runoff. [s] = 4 hours

    # ......-----------------------------------------------PIPES-----------------------------------------------......
    # Characteristics of the pipes that drain the catchments. Some are simplifications of catchments as pipes, others are actual pipes. The theory remains the same for both cases.
    # All the characteristics are vectors of the size of number of pipes that we are analysing. There can be a different number of pipes than catchments.
    # In this case, the first value of every vector belongs to the total catchment, the rest are from the internal pipes that are part of it.

    # The material of every pipe. [(m^1/3)/s]. The hypothesis here is that they are all the same material.
    strickler_coefficient = 75

    # ......-----------------------------------------------OVERFLOW-----------------------------------------------......

    # Q_lim = 0.4  # The flow after which there is a spill of the sewage. [m^3/s]
    # law = "yes"  # Do we know a threshold law ? Aswer can only be "yes" or "no". [str]
    # threshold_law = (
    #     "Q - 0.3263 * math.log(Q)- 0.68888"  # This equation should be written in terms of Q. It is a text. [str]
    # )

    ###### Fin de l'ajout provisoire

    # The code is divided in 12 steps from which only the first 4 should be edited by the user.

    num_sWS = len(catchment_surface)
    num_pipes = len(slope_pipe)
    law = "yes"  # Do we know a threshold law ? Aswer can only be "yes" or "no". [str]

    # Step 5: Adapt to the study period.

    # The available databases are usually larger than the study period of interest. At this step, the data that correspond to the study period will
    # be extracted from the full databases.

    (rain_time, rain_intensity, obs_time, obs_flow, obs_weir, full_study_period,) = MIG_TOOLBOX.USE_PERIOD(
        rain_file,
        rain_time_col_name,
        rain_intensity_col_name,
        observations_file,
        obs_time_col_name,
        obs_flow_col_name,
        obs_weir_col_name,
        starting_date,
        ending_date,
        time_step,
    )
    # rain_time = The observed rain time from the data base that is within the limits of the study period. List in datetime.datetime format.
    # rain_intensity = The observed intensity from the data base within the limits of the study period. List in mm/min.
    # obs_time = The observations time from the data base that is within the limits of the study period. List in datetime.datetime format.
    # obs_flow = The observed flow from the data base that is within the limits of the study period. List in m^3/s
    # obs_weir = The observed weir from the data base that is within the limits of the study period. List in m^3/s
    # full_study_period = Exhaustive list from starting date to ending date following the selected time step. List in datetime.datetime format.

    # Step 6: Definition of the upstream generated by every sWS. Use of the Rational method.

    # The main result from this step is the flow produced by every subwatershed that will enter the pipe.
    # THIS FLOW HAS NOT BEN TRANSFERED TO THE OUTFLOW. It is in an "upstream" position right at the entrance of the pipe.

    # The next lists are generated to be later filled. After the "for" cycle, each one is clearly explained.
    effective_intensities = []
    rain_types = []
    num_rains = []
    Q_up_imp_before = []
    Q_up_imp_after = []
    Q_up_per = []
    Q_up_WW = []
    Q_up_RII = []
    Q_up_PII = []

    # This repeats the instruction for every catchment to analyse. This way the results are produced for every subwatershed and stored in a same variable.
    for i in range(num_sWS):
        # The function is run for every catchment. Its results are stored in temporary lists that are replaced after every use.
        (
            effective_intensities_list,
            rain_types_list,
            num_rains_list,
            Q_up_imp_before_list,
            Q_up_imp_after_list,
            Q_up_per_list,
            Q_up_WW_list,
            Q_up_RII_list,
            Q_up_PII_list,
        ) = MIG_UPSTREAM_FLOW.UPSTREAM_FLOW(
            rain_time,
            rain_intensity,
            full_study_period,
            wastewater_pattern,
            ww_time_col_name,
            ww_flow_col_name,
            time_between_rains_runoff,
            catchment_surface[i],
            p_imp_surface[i],
            p_des_surface[i],
            hab[i],
            PE[i],
            PII[i],
            FRII[i],
            KRII[i],
            FIMP[i],
            FPER[i],
            IL[i],
            Hinf[i],
            Hsoil[i],
        )

        # The results are added to the list
        effective_intensities.append(effective_intensities_list)
        rain_types.append(rain_types_list)
        num_rains.append(num_rains_list)
        Q_up_imp_before.append(Q_up_imp_before_list)
        Q_up_imp_after.append(Q_up_imp_after_list)
        Q_up_per.append(Q_up_per_list)
        Q_up_WW.append(Q_up_WW_list)
        Q_up_RII.append(Q_up_RII_list)
        Q_up_PII.append(Q_up_PII_list)

    # effective_intensities = The effective intensities after removing the initial losses of ever sWS. There are three for every watershed: for permeable surface,
    # ------------------------impermeable surface and for the surface that produces the Induced Infiltration (II). This occurs because they all have different.
    # ------------------------Initial Losses to be removed. This is a list in mm/min.
    # rain_types = The list of the rain type for every moment measured by the pluviometer. This is a list the same length as the rain_time with the tags
    # ------------ "small", "medium" or "big" depending on the rain type at every instant. It is done for every catchment since the limits of small and big rain can change
    # ------------ between them. There are two for every sWS : runoff rain type and II rain type.
    # num_rains = This counts the number of rain events. Since there are two types of rain, for runoff and for II, every catchment will have two numbers of rains. This is due
    # ----------- to the difference in the definition of the dry period to consider two rains to be separated for runoff (4h) and infiltration (KRII).
    # Q_up_imp_before =  The runoff flow from impermeable surfaces that enters the sewage system in every watershed before the intervention. Lists in m3/s.
    # Q_up_imp_after = The runoff flow from impermeable surfaces that enters the sewage system in every watershed after the intervention. Lists in m3/s.
    # Q_up_per = The runoff flow from permeable surfaces that enters the sewage system in every watershed. The hypothesis is that it remains constant before and after the intervention. Lists in m3/s.
    # Q_up_WW = The wastewater flow from that enters the sewage system in every watershed. The hypothesis is that it remains constant before and after the intervention. Lists in m3/s.
    # Q_up_RII = The Rain Induced Infiltration flow that enters the sewage system in every watershed. The hypothesis is that it remains constant before and after the intervention. Lists in m3/s.
    # Q_up_PII = The Permanent Inflow Infiltration flow that enters the sewage system in every watershed. The hypothesis is that it remains constant before and after the intervention. Lists in m3/s.

    # Step 7: Apply the transfer function

    # Until now we have the six flows produced by every catchment that enter the pipe:
    # Runoff from impermeable surfaces before the intervention
    # Runoff from impermeable surfaces after the intervention
    # Runoff from permeable surfaces
    # Wastewater from the population
    # Rain Induced Infiltration flow (RII)
    # Permanent Inflow Infiltration flow (PII)

    # This point is called "upstream". Now the code will transfer this flows to the exit of the general catchment.

    # .....-------------BEFORE THE INTERVENTION----------------...
    Q_down_imp_before = MIG_TRANSFERED_FLOW.TRANSFERED_FLOW(
        num_sWS,
        Q_up_imp_before,
        pipe_order,
        num_pipes,
        decision,
        K,
        length_pipe,
        catchment_surface,
        p_imp_surface,
        slope_pipe,
        time_step,
    )

    # .....-------------AFTER THE INTERVENTION----------------...
    Q_down_imp_after = MIG_TRANSFERED_FLOW.TRANSFERED_FLOW(
        num_sWS,
        Q_up_imp_after,
        pipe_order,
        num_pipes,
        decision,
        K,
        length_pipe,
        catchment_surface,
        p_imp_surface,
        slope_pipe,
        time_step,
    )

    # ----------------UNAFFECTED BY THE INTERVENTION---------------------------------------
    Q_down_per = MIG_TRANSFERED_FLOW.TRANSFERED_FLOW(
        num_sWS,
        Q_up_per,
        pipe_order,
        num_pipes,
        decision,
        K,
        length_pipe,
        catchment_surface,
        p_imp_surface,
        slope_pipe,
        time_step,
    )

    Q_down_WW = MIG_TRANSFERED_FLOW.TRANSFERED_FLOW(
        num_sWS,
        Q_up_WW,
        pipe_order,
        num_pipes,
        decision,
        K,
        length_pipe,
        catchment_surface,
        p_imp_surface,
        slope_pipe,
        time_step,
    )

    Q_down_RII = MIG_TRANSFERED_FLOW.TRANSFERED_FLOW(
        num_sWS,
        Q_up_RII,
        pipe_order,
        num_pipes,
        decision,
        K,
        length_pipe,
        catchment_surface,
        p_imp_surface,
        slope_pipe,
        time_step,
    )

    Q_down_PII = MIG_TRANSFERED_FLOW.TRANSFERED_FLOW(
        num_sWS,
        Q_up_PII,
        pipe_order,
        num_pipes,
        decision,
        K,
        length_pipe,
        catchment_surface,
        p_imp_surface,
        slope_pipe,
        time_step,
    )

    # Q_down_imp_before =  The runoff flow of every sWS from impermeable surfaces before the intervention at the general outflow. Lists in m3/s.
    # Q_down_imp_after = The runoff flow of every sWS from impermeable surfaces after the intervention at the general outflow. Lists in m3/s.
    # Q_down_per = The runoff flow of every sWS from permeable surfaces at the general outflow. Lists in m3/s.
    # Q_down_WW = The wastewater flow of every sWS at the general outflow. Lists in m3/s.
    # Q_down_RII = The Rain Induced Infiltration flow of every sWS at the general outflow. Lists in m3/s.
    # Q_down_PII = The Permanent Inflow Infiltration flow of every sWS at the general outflow. Lists in m3/s.

    # Now the six flows produced by every catchment have been transfered the outflow of the whole study area.

    # Step 8: Add the flows in the outflow for the sub water catchments.

    # At this point we will add the flows of every subcatchment at the outflow of the whole study area.
    # This way we will have the total flow produced by every sub watershed at the general outflow.

    Q_down_all_before = (
        []
    )  # We initialize a list to be filled with the total flow downstream of every subwater catchment before the intervention.
    Q_down_all_after = (
        []
    )  # We initialize a list to be filled with the total flow downstream of every subwater catchment after the intervention.

    for j in range(num_sWS):
        Q_down_all_before_list = []
        Q_down_all_after_list = []
        for i in range(len(full_study_period)):
            Q_down_all_before_list.append(
                Q_down_imp_before[j][i] + Q_down_per[j][i] + Q_down_WW[j][i] + Q_down_RII[j][i] + Q_down_PII[j][i]
            )
            Q_down_all_after_list.append(
                Q_down_imp_after[j][i] + Q_down_per[j][i] + Q_down_WW[j][i] + Q_down_RII[j][i] + Q_down_PII[j][i]
            )
        Q_down_all_before.append(Q_down_all_before_list)
        Q_down_all_after.append(Q_down_all_after_list)

    # Q_down_all_before = The list with the total flow downstream of every subwater catchment. Before the intervention. Lists in m3/s
    # Q_down_all_after = The list with the total flow downstream of every subwater catchment. After the intervention. Lists in m3/s

    # Now we have the total flow at the exit of the catchment for every subcatchment, including the general one.
    # The result is two lists (One before intervention and one after intervention) in which every element contains the full flow list for every subcatchment.
    # Keep in mind that the first element (i=0) is the one that belongs to the general catchment. If there is only one catchment in study, this is the only element.

    Q_down_general_before = Q_down_all_before[0]  # Generates a list aside for this flow.
    Q_down_general_after = Q_down_all_after[0]  # Generates a list aside for this flow.

    # Q_down_general_before = The total flow at the outflow produced by the general model before the intervention. List in m3/s
    # Q_down_general_after = The total flow at the outflow produced by the general model after the intervention. List in m3/s

    # In case there is more than one catchment. This is for cases with subcatchments. This will add all the flows of all the sub watersheds.
    # This would represent the total flow produced by all the sWS together.
    if num_sWS > 1:
        Q_down_sum_before = []
        Q_down_sum_after = []

        for i in range(len(full_study_period)):
            Q_down_sum_before_list = []
            Q_down_sum_after_list = []
            for j in range(1, num_sWS):
                Q_down_sum_before_list.append(Q_down_all_before[j][i])
                Q_down_sum_after_list.append(Q_down_all_after[j][i])
            Q_down_sum_before.append(sum(Q_down_sum_before_list))
            Q_down_sum_after.append(sum(Q_down_sum_after_list))

    # Q_down_sum_before = The added flow of the different watercatchments at the exit point. Before the intervention. List in m3/s
    # Q_down_sum_after = The added flow of the different watercatchments at the exit point. After the intervention. List in m3/s

    # We have the added flow of all the sub catchmnts that make up the general one.

    # Step 9: Show which watersheds produce the most water.

    # At this point we will rank all the watersheds according to the volume of water they produce.

    # We define the volume produced by the whole catchment using the subdivision.
    V_down_sum_before = (
        sum(Q_down_sum_before) * time_step * 60
    )  # This is multiplied by 60 to transform the dt(min) in seconds.
    V_down_sum_after = (
        sum(Q_down_sum_after) * time_step * 60
    )  # This is multiplied by 60 to transform the dt(min) in seconds.

    # V_down_sum_before = The total volume produced by the all the subwatersheds at the output before the intervention. Result in m3.
    # V_down_sum_after = The total volume produced by the all the subwatersheds at the output before the intervention. Result in m3.

    # We sort the subwatersheds in decreasing order according to their volume production For this, we use a dictionary.

    V_sWS = {}
    V_sWS_sort = []
    for i in range(num_sWS):
        V_sWS[i] = sum(Q_down_all_before[i]) * time_step * 60

    V_sWS_sort = sorted(V_sWS.items(), key=lambda x: x[1], reverse=True)

    # Step 10: Verify if there are any spills.

    # This is done for both the full catchment and the discretized model.

    # --------------FOR THE FULL CATCHMENT------------------
    (
        Q_weir_general_before,
        spill_dates_general_before,
        num_spills_general_before,
    ) = MIG_TOOLBOX.OVERFLOW(law, Q_down_general_before, full_study_period, Q_lim, threshold_law)

    (
        Q_weir_general_after,
        spill_dates_general_after,
        num_spills_general_after,
    ) = MIG_TOOLBOX.OVERFLOW(law, Q_down_general_after, full_study_period, Q_lim, threshold_law)

    # Q_weir_general_before = The weir flow for the general model before the intervention. List in m3/s
    # spill_dates_general_before = The list of dates where there was a spill for the general model before the intervention.
    # num_spills_general_before = The total number of overflows for the general model before the intervention.
    # Q_weir_general_after = The weir flow for the general model after the intervention. List in m3/s
    # spill_dates_general_after = The list of dates where there was a spill for the general model after the intervention.
    # num_spills_general_after = The total number of overflows for the general model after the intervention.

    # --------------FOR THE DISCRETIZED MODEL------------------

    # If it exists
    if num_sWS > 1:
        (
            Q_weir_sum_before,
            spill_dates_sum_before,
            num_spills_sum_before,
        ) = MIG_TOOLBOX.OVERFLOW(law, Q_down_sum_before, full_study_period, Q_lim, threshold_law)

        (
            Q_weir_sum_after,
            spill_dates_sum_after,
            num_spills_sum_after,
        ) = MIG_TOOLBOX.OVERFLOW(law, Q_down_sum_after, full_study_period, Q_lim, threshold_law)

        # Q_weir_sum_before = The weir flow for the general model before the intervention. List in m3/s
        # spill_dates_sum_before = The list of dates where there was a spill for the general model before the intervention.
        # num_spills_sum_before = The total number of overflows for the general model before the intervention.
        # Q_weir_sum_after = The weir flow for the general model after the intervention. List in m3/s
        # spill_dates_sum_after = The list of dates where there was a spill for the general model after the intervention.
        # num_spills_sum_after = The total number of overflows for the general model after the intervention.

    # Step 11: Plots the found data and save it

    # We define a list with many colors (In this case 8)
    colors = ["green", "yellow", "magenta", "orange", "lime", "purple", "pink", "navy"]

    # We define a list as long as the full_study_period that has the value of the overflow limit (Q_lim)
    Seuil = [Q_lim for i in range(len(full_study_period))]

    # Two functions are imported. Done at this point because if done at the beginning does not work well; just a bug.
    import matplotlib.dates as mdates
    from matplotlib.dates import HourLocator

    # BEFORE THE INTERVENTION - SUM OF EVERY SUB WATERSHED
    # Now we provide the general information for all the plots
    fig, ax = plt.subplots(1, dpi=150)
    fig.autofmt_xdate()

    # Plots in the same graph
    plt.plot(full_study_period, Q_down_sum_before, linestyle="-", color="blue", lw=1.0)
    plt.plot(full_study_period, Seuil, linestyle="-", color="red", lw=1.0)
    plt.plot(obs_time, obs_flow, color="black", lw=1, linestyle="-")

    lege = []
    for i in range(1, num_sWS):
        plt.plot(
            full_study_period,
            Q_down_all_before[i],
            linestyle="-",
            color=colors[i],
            lw=1.0,
        )
        lege.append("sWS " + str(i))

    # Title and lables
    Graph_title = "Sum all watersheds Vs. Flow Observation - before intervention"
    plt.title(Graph_title)
    plt.ylabel("Flow [m$^{3}$/s]")
    plt.xlabel("Time")

    # Function add a legend
    lege = ["Simulation", "Overflow limit", "Observations"] + lege
    plt.legend(lege)

    # Modify mes bars
    axes = plt.gca()
    axes.xaxis.set_ticks(full_study_period)
    axes.xaxis.set_ticklabels(
        full_study_period,
        rotation=45,
        color="black",
        fontsize="9",
        style="normal",
        verticalalignment="top",
    )
    ax.set(ylim=(0, max(Q_down_sum_before) + 0.1))

    # Format the date and time
    xfmt = mdates.DateFormatter("%d-%m-%Y %H:%M")
    ax.xaxis.set_major_formatter(xfmt)

    plt.minorticks_on()
    plt.grid(which="major", axis="x", linestyle=":", linewidth="0.5", color="silver")
    plt.grid(
        which="minor",
        axis="x",
        linestyle=":",
        linewidth="0.1",
        color="lightgrey",
        label=False,
    )

    ax.tick_params(
        which="both",  # Options for both major and minor ticks
        top="on",  # turn off top ticks
        left="off",  # turn off left ticks
        right="off",  # turn off right ticks
        bottom="on",
    )  # turn off bottom ticks

    # GRID with a certain interval
    ax.xaxis.set_major_locator(HourLocator(byhour=None, interval=6, tz=None))

    # Save

    fig_name = str(path_csv) + "/PLOT_GENERAL_BEFORE.png"
    plt.savefig(str(fig_name), dpi=150)

    # AFTER THE INTERVENTION - SUM OF EVERY SUB WATERSHED

    # Now we provide the general information for all the plots
    fig, ax = plt.subplots(1, dpi=150)
    fig.autofmt_xdate()

    # Plots in the same graph
    plt.plot(full_study_period, Q_down_sum_after, linestyle="-", color="blue", lw=1.0)
    plt.plot(full_study_period, Seuil, linestyle="-", color="red", lw=1.0)
    plt.plot(obs_time, obs_flow, color="black", lw=1, linestyle="-")

    lege = []
    for i in range(1, num_sWS):
        plt.plot(
            full_study_period,
            Q_down_all_after[i],
            linestyle="-",
            color=colors[i],
            lw=1.0,
        )
        lege.append("sWS " + str(i))

    # Title and lables
    Graph_title = "Sum all watersheds Vs. Flow Observation - after intervention"
    plt.title(Graph_title)
    plt.ylabel("Flow [m$^{3}$/s]")
    plt.xlabel("Time")

    # Function add a legend
    lege = ["Simulation", "Overflow limit", "Observations"] + lege
    plt.legend(lege)

    # Modify mes bars
    axes = plt.gca()
    axes.xaxis.set_ticks(full_study_period)
    axes.xaxis.set_ticklabels(
        full_study_period,
        rotation=45,
        color="black",
        fontsize="9",
        style="normal",
        verticalalignment="top",
    )
    ax.set(ylim=(0, max(Q_down_sum_after) + 0.1))

    # Format the date and time
    xfmt = mdates.DateFormatter("%d-%m-%Y %H:%M")
    ax.xaxis.set_major_formatter(xfmt)

    plt.minorticks_on()
    plt.grid(which="major", axis="x", linestyle=":", linewidth="0.5", color="silver")
    plt.grid(
        which="minor",
        axis="x",
        linestyle=":",
        linewidth="0.1",
        color="lightgrey",
        label=False,
    )

    ax.tick_params(
        which="both",  # Options for both major and minor ticks
        top="on",  # turn off top ticks
        left="off",  # turn off left ticks
        right="off",  # turn off right ticks
        bottom="on",
    )  # turn off bottom ticks

    # GRID with a certain interval
    ax.xaxis.set_major_locator(HourLocator(byhour=None, interval=6, tz=None))

    # Save
    fig_name = str(path_csv) + "/PLOT_GENERAL_AFTER.png"
    plt.savefig(str(fig_name), dpi=150)  # FIXME: pour l'instant pas de diff avant/apres

    # BEFORE THE INTERVENTION - EVERY SUB WATERSHED

    for i in range(num_sWS):
        # Now we provide the general information for all the plots
        fig, ax = plt.subplots(1, dpi=150)
        fig.autofmt_xdate()

        # Plots in the same graph
        plt.plot(
            full_study_period,
            Q_down_imp_before[i],
            linestyle="-",
            color="purple",
            lw=1.0,
        )
        plt.plot(full_study_period, Q_down_per[i], linestyle="-", color="blue", lw=1.0)
        plt.plot(full_study_period, Q_down_WW[i], linestyle="-", color="red", lw=1.0)
        plt.plot(full_study_period, Q_down_RII[i], linestyle="-", color="magenta", lw=1.0)
        plt.plot(full_study_period, Q_down_PII[i], linestyle="-", color="cyan", lw=1.0)
        plt.plot(
            full_study_period,
            Q_down_all_before[i],
            linestyle="-",
            color="orange",
            lw=1.0,
        )

        # Title and lables
        Graph_title = "sWS " + str(i) + " Before Intervention "
        plt.title(Graph_title)
        plt.ylabel("Flow [m$^{3}$/s]")
        plt.xlabel("Time")

        # Function add a legend
        plt.legend(
            [
                "Impermeable Runoff",
                "Permeable Runoff",
                "Wastewater",
                "RII",
                "PII",
                "Total outlet flow",
                "Observations",
            ]
        )

        # Modify mes bars
        axes = plt.gca()
        axes.xaxis.set_ticks(full_study_period)
        axes.xaxis.set_ticklabels(
            full_study_period,
            rotation=45,
            color="black",
            fontsize="9",
            style="normal",
            verticalalignment="top",
        )
        ax.set(ylim=(0, max(Q_down_all_before[i]) + 0.1))

        # Format the date and time
        xfmt = mdates.DateFormatter("%d-%m-%Y %H:%M")
        ax.xaxis.set_major_formatter(xfmt)

        plt.minorticks_on()
        plt.grid(which="major", axis="x", linestyle=":", linewidth="0.5", color="silver")
        plt.grid(
            which="minor",
            axis="x",
            linestyle=":",
            linewidth="0.1",
            color="lightgrey",
            label=False,
        )

        ax.tick_params(
            which="both",  # Options for both major and minor ticks
            top="on",  # turn off top ticks
            left="off",  # turn off left ticks
            right="off",  # turn off right ticks
            bottom="on",
        )  # turn off bottom ticks

        # GRID with a certain interval
        ax.xaxis.set_major_locator(HourLocator(byhour=None, interval=6, tz=None))

        # Save
        fig_name = str(path_csv) + f"/PLOT_sBV_{i}_before.png"
        plt.savefig(str(fig_name), dpi=150)

    # AFTER THE INTERVENTION - EVERY SUB WATERSHED

    for i in range(num_sWS):
        # Now we provide the general information for all the plots
        fig, ax = plt.subplots(1, dpi=150)
        fig.autofmt_xdate()

        # Plots in the same graph
        plt.plot(
            full_study_period,
            Q_down_imp_after[i],
            linestyle="-",
            color="purple",
            lw=1.0,
        )
        plt.plot(full_study_period, Q_down_per[i], linestyle="-", color="blue", lw=1.0)
        plt.plot(full_study_period, Q_down_WW[i], linestyle="-", color="red", lw=1.0)
        plt.plot(full_study_period, Q_down_RII[i], linestyle="-", color="magenta", lw=1.0)
        plt.plot(full_study_period, Q_down_PII[i], linestyle="-", color="cyan", lw=1.0)
        plt.plot(
            full_study_period,
            Q_down_all_after[i],
            linestyle="-",
            color="orange",
            lw=1.0,
        )

        # Title and lables
        Graph_title = "sWS " + str(i) + " After Intervention"
        plt.title(Graph_title)
        plt.ylabel("Flow [m$^{3}$/s]")
        plt.xlabel("Time")

        # Function add a legend
        plt.legend(
            [
                "Impermeable Runoff",
                "Permeable Runoff",
                "Wastewater",
                "RII",
                "PII",
                "Total outlet flow",
                "Observations",
            ]
        )

        # Modify mes bars
        axes = plt.gca()
        axes.xaxis.set_ticks(full_study_period)
        axes.xaxis.set_ticklabels(
            full_study_period,
            rotation=45,
            color="black",
            fontsize="9",
            style="normal",
            verticalalignment="top",
        )
        ax.set(ylim=(0, max(Q_down_all_before[i]) + 0.1))

        # Format the date and time
        xfmt = mdates.DateFormatter("%d-%m-%Y %H:%M")
        ax.xaxis.set_major_formatter(xfmt)

        plt.minorticks_on()
        plt.grid(which="major", axis="x", linestyle=":", linewidth="0.5", color="silver")
        plt.grid(
            which="minor",
            axis="x",
            linestyle=":",
            linewidth="0.1",
            color="lightgrey",
            label=False,
        )

        ax.tick_params(
            which="both",  # Options for both major and minor ticks
            top="on",  # turn off top ticks
            left="off",  # turn off left ticks
            right="off",  # turn off right ticks
            bottom="on",
        )  # turn off bottom ticks

        # GRID with a certain interval
        ax.xaxis.set_major_locator(HourLocator(byhour=None, interval=6, tz=None))

        # Save
        fig_name = str(path_csv) + f"/PLOT_sBV_{i}_after.png"
        plt.savefig(str(fig_name), dpi=150)  # FIXME: pour l'instant pas de diff avant/apres

    # Step 12: Save the data into files

    # For everything to be in the same date and time, the observation flows and overflows are filled

    # First we fill the wholes in the list with "ND".
    full_obs_flow = MIG_TOOLBOX.COMPLETE_STUDY_PERIOD(obs_time, full_study_period, obs_flow, "ND")
    full_obs_weir = MIG_TOOLBOX.COMPLETE_STUDY_PERIOD(obs_time, full_study_period, obs_weir, "ND")

    # For the general results
    # We define the headers of the file
    headers = [
        [
            "date",
            "Obs_flow",
            "Q_general_before",
            "Q_general_after",
            "Q_sum_before",
            "Q_sum_after",
            "Obs_weir",
            "Q_weir_general_before",
            "Q_weir_general_after",
            "Q_weir_sum_before",
            "Q_weir_sum_after",
        ]
    ]

    # We define the data that will be added
    List_data = [
        full_study_period,
        full_obs_flow,
        Q_down_general_before,
        Q_down_general_after,
        Q_down_sum_before,
        Q_down_sum_after,
        full_obs_weir,
        Q_weir_general_before,
        Q_weir_general_after,
        Q_weir_sum_before,
        Q_weir_sum_after,
    ]

    # We create the file
    export_data = zip_longest(*List_data, fillvalue=" ")
    with (Path(path_csv) / "RESULTAT_TOTAL.csv").open("w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerows(headers)
        writer.writerows(export_data)

    # For the results of every subcatchment
    # We define the headers of the file
    for i in range(num_sWS):
        headers = [
            [
                "date",
                "Q_down_imp_before",
                "Q_down_imp_after",
                "Q_down_per",
                "Q_down_WW",
                "Q_down_RII",
                "Q_down_PII",
                "Total outlet flow before",
                "Total outlet flow after",
            ]
        ]

        # We define the data that will be added
        List_data = [
            full_study_period,
            Q_down_imp_before[i],
            Q_down_imp_after[i],
            Q_down_per[i],
            Q_down_WW[i],
            Q_down_RII[i],
            Q_down_PII[i],
            Q_down_all_before[i],
            Q_down_all_after[i],
        ]

        # We create the file
        export_data = zip_longest(*List_data, fillvalue=" ")
        with (Path(path_csv) / f"RESULTAT_sWS{i}.csv").open("w", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerows(headers)
            writer.writerows(export_data)

    return V_sWS
