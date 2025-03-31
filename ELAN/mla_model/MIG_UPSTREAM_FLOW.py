# pylint: skip-file

"""
The aim of this code is to simulate the flow of a catchment after it has rained. This flow enters the municipal sewage syste so it
considers both superfitial runnoff and infiltration flow in the pipes. The rational method is used in both cases.

The final result is the superfitial and infiltration flow that are produced in the catchment without them having goine through the
linear reservoir method. We can call these as the "usptream" flows.

The code also provides the list of effective intensities, rain types, number of rains and individual flows.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 26/04/2023
"""

from . import MIG_II, MIG_RUNOFF_PRODUCTION, MIG_WASTEWATER


def UPSTREAM_FLOW(
    rain_time,
    intensity_period,
    full_study_period,
    wastewater_pattern,
    ww_time_col_name,
    ww_flow_col_name,
    time_between_rains_runoff,
    catchment_surface,
    p_imp_surface,
    p_desimp_surface,
    hab,
    EH,
    PII,
    FRII,
    KRII,
    FIMP,
    FPER,
    IL,
    Hinf,
    Hsoil,
):
    # Step 1: Defines the parts of the catchment
    imp_surface_before = catchment_surface * p_imp_surface  # Result of impermeable surface in ha BEFORE INTERVENTION
    per_surface = catchment_surface - imp_surface_before  # Result of permeable surface in ha
    desimp_surface = imp_surface_before * p_desimp_surface  # Result of dewaterproofed surface in ha
    p_per_surface = per_surface / catchment_surface  # Percentage of permeable surface in the catchment
    imp_surface_after = imp_surface_before - desimp_surface  # Result of impermeable surface in ha AFTER INTERVENTION

    # Step 2: Generated runoff
    (
        imp_effective_intensity,
        per_effective_intensity,
        runoff_rain_type,
        runoff_num_rains,
        Q_up_imp_before,
        Q_up_imp_after,
        Q_up_per,
    ) = MIG_RUNOFF_PRODUCTION.RUNOFF_PRODUCTION(
        p_imp_surface,
        imp_surface_before,
        p_per_surface,
        per_surface,
        imp_surface_after,
        IL,
        Hinf,
        Hsoil,
        FIMP,
        FPER,
        rain_time,
        intensity_period,
        full_study_period,
        time_between_rains_runoff,
    )

    # imp_effective_intensity = The effective intensiry of the rain in the impermeable surfaces after removing the initial losses. List in mm/min.
    # per_effective_intensity = The effective intensiry of the rain in the permeable surfaces after removing the initial losses. List in mm/min.
    # runoff_rain_type = List that says the type of rain for every rain_time step. Only includes "small", "medium" or "big".
    # num_rains = number or fain events considering the dry time between rains.
    # Q_up_imp_before = The runoff of the impermeable surface before the intervention. List in m3/s. During all the study period.
    # Q_up_imp_after = The runoff of the impermeable surface after the intervention. List in m3/s. During all the study period.
    # Q_up_per = The runoff of the permeable surface. List in m3/s. During all the study period.

    # Step 3: Generated Wastewater in the catchment
    Q_up_WW = MIG_WASTEWATER.WASTEWATER(
        wastewater_pattern, ww_time_col_name, ww_flow_col_name, full_study_period, hab, EH
    )
    # Q_up_WW = The generated wastewater by the population living in the catchment. List in m3/s. During all the study period.

    # Step 4: Generate the Inflow Infiltration - II
    II_effective_intensity, II_rain_type, II_num_rains, Q_up_RII, Q_up_PII = MIG_II.II(
        rain_time, full_study_period, intensity_period, Hinf, Hsoil, per_surface, p_per_surface, PII, FRII, KRII
    )

    # II_effective_intensity = The effective intensiry of the rain for inflow infiltration after removing the initial losses. List in mm/min.
    # II_rain_type = List that says the type of rain for every rain_time step under infiltration parameters. Only includes "small", "medium" or "big".
    # II_num_rains = Number of rains under the infiltration parameters.
    # Q_up_RII = Rain Induced Infiltration flow upstream before going through the pipe. List in m3/s. During all the study period.
    # Q_up_PII = Permanent Inflow Infiltration flow upstream before going through the pipe. List in m3/s. During all the study period.

    # Step 5: Group the results to be presented
    effective_intensities = imp_effective_intensity, per_effective_intensity, II_effective_intensity
    rain_types = runoff_rain_type, II_rain_type
    num_rains = runoff_num_rains, II_num_rains

    return (
        effective_intensities,
        rain_types,
        num_rains,
        Q_up_imp_before,
        Q_up_imp_after,
        Q_up_per,
        Q_up_WW,
        Q_up_RII,
        Q_up_PII,
    )
