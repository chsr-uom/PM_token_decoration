# Import necessary libraries from PM4Py. These libraries provide functionality for process mining and visualization.
from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
from pm4py.statistics.variants.log import get as variants_get
from pm4py.visualization.petrinet.common import visualize
from pm4py.visualization.petrinet.util import performance_map
from pm4py.util import exec_utils, xes_constants
from pm4py.visualization.petrinet.parameters import Parameters


# Function to calculate decorations. Decorations are additional information 
# that can be used to annotate a Petri net. In this case, the decorations 
# represent performance or frequency measurements for different aspects of the process.
def get_decorations(log, net, initial_marking, final_marking, parameters=None, measure="frequency",
                    ht_perf_method="last"):
    """
    Calculate decorations in order to annotate the Petri net

    Parameters
    -----------
    log
        Trace log
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    parameters
        Parameters associated to the algorithm
    measure
        Measure to represent on the process model (frequency/performance)
    ht_perf_method
        Method to use in order to annotate hidden transitions (performance value could be put on the last possible
        point (last) or in the first possible point (first)

    Returns
    ------------
    decorations
        Decorations to put on the process model
    """
    # If no parameters are provided, initialize an empty dictionary
    if parameters is None:
        parameters = {}

    # The following lines retrieve various parameters that will be used in the function.
    # If these parameters are not provided, default values are used.
    aggregation_measure = exec_utils.get_param_value(Parameters.AGGREGATION_MEASURE, parameters, None)
    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    timestamp_key = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                               xes_constants.DEFAULT_TIMESTAMP_KEY)

    # The next two lines get a list of the variants in the log. 
    # Variants are different sequences of activities that occur in the log.
    variants_idx = variants_get.get_variants_from_log_trace_idx(log, parameters=parameters)
    variants = variants_get.convert_variants_trace_idx_to_trace_obj(log, variants_idx)

    # Setting parameters for token replay. Token replay is a conformance checking 
    # technique that is used to compare the observed behavior (log) with the modeled behavior (Petri net).
    parameters_tr = {token_replay.Variants.TOKEN_REPLAY.value.Parameters.ACTIVITY_KEY: activity_key,
                     token_replay.Variants.TOKEN_REPLAY.value.Parameters.VARIANTS: variants}

    # The token replay algorithm is applied to the log and the Petri net. 
    # This provides a list of aligned traces which contain information about 
    # which sequences of activities in the log conform to the model and which do not.
    aligned_traces = token_replay.apply(log, net, initial_marking, final_marking, parameters=parameters_tr)

    # The following two lines calculate statistics for individual elements in the log 
    # and then aggregate these statistics. These statistics will form the basis of the decorations.
    element_statistics = performance_map.single_element_statistics(log, net, initial_marking,
                                                                   aligned_traces, variants_idx,
                                                                   activity_key=activity_key,
                                                                   timestamp_key=timestamp_key,
                                                                   ht_perf_method=ht_perf_method)

    aggregated_statistics = performance_map.aggregate_statistics(element_statistics, measure=measure,
                                                                 aggregation_measure=aggregation_measure)

    # The function returns the aggregated statistics, which can be used as decorations.
    return aggregated_statistics


# Function to visualize the Petri net with performance indicators 
# obtained by the token replay algorithm.
def apply(net, initial_marking, final_marking, log=None, aggregated_statistics=None, parameters=None):
    """
    Apply method for Petri net visualization (it calls the graphviz_visualization
    method) adding performance representation obtained by token replay

    Parameters
    -----------
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    log
        (Optional) log
    aggregated_statistics
        Dictionary containing the frequency statistics
    parameters
        Algorithm parameters (including the activity key used during the replay, and the timestamp key)

    Returns
    -----------
    viz
        Graph object
    """
    # If no aggregated statistics are provided and a log is available, 
    # the get_decorations function is called to calculate these statistics.
    if aggregated_statistics is None:
        if log is not None:
            aggregated_statistics = get_decorations(log, net, initial_marking, final_marking, parameters=parameters,
                                                    measure="custom")
    
    # The visualization is created with the given Petri net and markings, 
    # and the aggregated statistics are used as decorations. 
    # The resulting graph object is returned.
    return visualize.apply(net, initial_marking, final_marking, parameters=parameters,
                           decorations=aggregated_statistics)
