# pylint: skip-file

"""
This code takes a flow list and transfers it through a pipe by using the linear reservoir method.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 04/05/2023
"""

from . import MIG_TOOLBOX


def TRANSFERED_FLOW(
    num_SBVs, flow, pipe_order, num_pipes, decision, K, length_pipe, catchment_surface, p_imp_surface, slope_pipe, dt
):
    Q_down = []  # This initializes an empty list to be filled with the flow downstream.

    for i in range(num_SBVs):
        Q_down_list = flow[i]
        # This takes the upstream flow as the entry for the first pipe.

        # This is the procedure if there is only one pipe.
        if type(pipe_order[i]) == int:
            for k in range(num_pipes):
                if pipe_order[i] == k:
                    Q_down_list = MIG_TOOLBOX.LINEAR_RESERVOIR(
                        decision[k],
                        K[k],
                        length_pipe[k],
                        catchment_surface[i],
                        p_imp_surface[i],
                        slope_pipe[k],
                        dt,
                        Q_down_list,
                    )

        # When there is more than one pipe.
        else:
            for j in range(len(pipe_order[i])):
                for k in range(num_pipes):
                    if pipe_order[i][j] == k:
                        Q_down_list = MIG_TOOLBOX.LINEAR_RESERVOIR(
                            decision[k],
                            K[k],
                            length_pipe[k],
                            catchment_surface[i],
                            p_imp_surface[i],
                            slope_pipe[k],
                            dt,
                            Q_down_list,
                        )
        # This last part takes the outflow of one pipe as the inflow for the next one until the ending of the system where the result is the final downstream flow.

        # It finally takes the last downstream flow. It is the flow at the outflow of the whole system.

        Q_down.append(Q_down_list)
    return Q_down
