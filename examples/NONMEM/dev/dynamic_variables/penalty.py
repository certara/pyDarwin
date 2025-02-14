import os
import json
import logging
import sys
import pandas as pd
import numpy as np
import warnings

# Setup logging
logger = logging.getLogger(__name__)

# Reduce pandas warnings
warnings.filterwarnings(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None 

def get_penalty_weights():

    penalty_weights = {
        "param_estimates":
            [   
                {
                "name": "theta_relative_error",
                "type": "relative_error",
                "param": "theta",
                "thresholds_penalties": [
                    (10, 100000),
                    (0.75, 100),
                    (0.3, 20),
                    (0.1, 0)]
                }, 
                {
                "name": "omega_relative_error",
                "type": "relative_error",
                "param": "omega",
                "thresholds_penalties":[
                    (10, 100000),
                    (0.65, 100),
                    (0.4, 30),
                    (0.2, 0)]

                },
                {
                "name": "condition_number",
                "type": "condition_number",
                "param": "theta",
                "thresholds_penalties":[
                    (1000000, 10000000),
                    (10000, 1000),
                    (1000, 100),
                    (500, 0)]
                },
                {
                "name": "omega_estimated",
                "type": "estimated_values",
                "param": "omega",
                "thresholds_penalties":[
                    (3.5, 1000000),
                    (3, 10000),
                    (2.3, 500),
                    (1.65, 100),
                    (1, 0),
                    (0.01, 0),
                    (0.001, 1000),
                    (0, 1000000)]
                },
                {
                "name": "omega_shrinkage",
                "type": "shrinkage",
                "param": "omega",
                "thresholds_penalties":[
                    (100, 200),
                    (40, 0)
                    ],
                "ignore": ["CL", "V2"],
                "fix": False
                }
            ],
        "model_complexity":
            [
                {
                    "name": "theta_non_fixed_params",
                    "penalty": 10
                },
                {
                    "name": "omega_non_fixed_params",
                    "penalty": 10
                }, 
                {
                    "name": "sigma_non_fixed_params",
                    "penalty": 10
                },
                {
                    "name": "ncomp_transit",
                    "penalty": 10
                }, 
            ]
        }
    
    return penalty_weights


def post_process(run_dir):
    
    # Variable definition
    debug = False
    use_scaling_factor = False
    
    logger.debug("Running penalty function1")

    # Get control
    control = read_control(run_dir)

    # # Get lst file
    # lst = read_lst(run_dir)
    

    # Get penalty weights
    logger.debug("Get penalty weights")
    penalty_weights = get_penalty_weights()

    # Extract values from control
    out = count_params(control)
    params = out["params"]
    log_params = out["log_params"]
    fix_params = out["fix_params"]
    param_names = out["param_names"]

    # Save model param metrics
    # write_json_file(params, os.path.join(run_dir, "model_param_metrics.json"))

    # Get parameter penalty
    if "param_estimates" in penalty_weights:
        logger.debug("Calculate parameter estimate penalty")
        param_estimates = get_param_estimates(run_dir, log_params, fix_params, param_names)

        # If param estimate is None then run did not finish
        if param_estimates is None:
            penalty_weights["run_success"] = False
            param_estimate_penalty_score = 99999
            # return penalty_weights["total_penalty_score"], json.dumps(penalty_weights)
        else: # Run successfully finished
            penalty_weights["run_success"] = True
            param_estimate_penalty_score, df = calc_param_estimate_penalty(
                param_estimates, penalty_weights["param_estimates"])

            # Save param estimates
            file_name = os.path.join(run_dir, "param_estimates.csv")
            df.to_csv(file_name, index=False)
    else:
        param_estimate_penalty_score = 0

    # Get model complexity penalty
    if "model_complexity" in penalty_weights:
        logger.debug("Calculate model complexity penalty")
        model_complexity_penalty_score = calc_model_complexity_penalty(
            params, penalty_weights["model_complexity"])
        model_complex_path = os.path.join(run_dir, "model_complexity.csv")
        pd.DataFrame(penalty_weights["model_complexity"]).to_csv(model_complex_path, index=False)
    else:
        model_complexity_penalty_score = 0

    # Calculate total penalty
    penalty_weights["penalty_score_sum"] = model_complexity_penalty_score + param_estimate_penalty_score

    if use_scaling_factor:
        
        # Get data length
        data_length = get_data_length(control)

        # Calculate scaling factor
        scaling_factor = data_length / 2500
        penalty_weights["total_penalty_score"] = penalty_weights["penalty_score_sum"] * scaling_factor
    else:
        # Don't use scaling factor
        scaling_factor = 1
        penalty_weights["total_penalty_score"] = penalty_weights["penalty_score_sum"]
    
    if not debug:
        return penalty_weights["total_penalty_score"], json.dumps(penalty_weights)
    else:
        return penalty_weights["total_penalty_score"], json.dumps(penalty_weights), param_estimates


def get_data_length(control):


    data_len =  (
        control
        .split("TOTAL DATA POINTS NORMALLY DISTRIBUTED (N): ")[-1]
        .split("\n")[0]
        .strip())
    return int(data_len)



def get_param_estimates(run_dir, log_params, fix_params, param_names):
    
    # Get param estimates
    param_estimates = extract_parameter_estimates(run_dir)

    # If param_estimates is none then run did not finish
    if param_estimates is None:
        None
    else:
        param_estimates["log"] = None

        # Mark whether values have been log transformed
        for param_type in log_params.keys():
            param_estimates.loc[param_estimates['param_type'] == param_type, "log"] = log_params[param_type]
            param_estimates.loc[param_estimates['param_type'] == param_type, "fix"] = fix_params[param_type]
            param_estimates.loc[param_estimates['param_type'] == param_type, "name"] = param_names[param_type]

        # Calculate relative error
        param_estimates["relative_error"] = np.nan

        # Theta relative error
        m_theta = param_estimates["param_type"] == "theta"
        m_log = param_estimates["log"] == True

        param_estimates.loc[m_theta & ~m_log, "relative_error"] = abs(param_estimates["standard_error"] / param_estimates["estimated_values"])
        param_estimates.loc[m_theta & m_log, "relative_error"] = np.sqrt(np.exp(param_estimates.loc[m_theta & m_log, "standard_error"] ** 2) - 1)

        # Omega relative error
        m_omega = param_estimates["param_type"] == "omega"
        param_estimates.loc[m_omega, "relative_error"] = param_estimates["standard_error"] / param_estimates["estimated_values"] / 2

        # Sigma relative error
        m_sigma = param_estimates["param_type"] == "sigma"
        param_estimates.loc[m_sigma, "relative_error"] = param_estimates["standard_error"] / param_estimates["estimated_values"]
        
        param_estimates = param_estimates[["param_type", "name", "log", "fix", "i", "j", "estimated_values", "standard_error", "relative_error", "condition_number", "shrinkage"]]
        param_estimates["i"] = param_estimates["i"].astype(int)
        param_estimates["j"] = param_estimates["j"].astype(int)


        # Calculate real values

        # Real Theta & Sigma
        param_estimates["estimated_real"] = param_estimates["estimated_values"]
        param_estimates["units"] = ""

        m1 = param_estimates["log"]==True
        m2 = param_estimates["param_type"] == "theta"
        param_estimates.loc[m1 & m2, "estimated_real"] = np.exp(param_estimates["estimated_values"])

        # Real Omega
        m1 = param_estimates["param_type"] == "omega"
        param_estimates.loc[m1, "estimated_real"] = np.sqrt(np.exp(param_estimates.loc[m1, "estimated_values"]) - 1) * 100
        param_estimates.loc[m1, "units"] = "CV%"
        
        return param_estimates



def calc_param_estimate_penalty(param_estimates, param_estimate_weights):

    # logger.debug(f"Logger test")
    
    penalty_score = 0

    # Load param estimate penalties
    weights = pd.DataFrame(param_estimate_weights)

    # Unpack thresholds and penalties
    thresholds_all = []
    penalties_all = []
    for i, row in weights.iterrows():
        thresholds = [x[0] for x in row["thresholds_penalties"]]
        penalties = [x[1] for x in row["thresholds_penalties"]]
        thresholds_all.append(thresholds)
        penalties_all.append(penalties)
    weights["thresholds"] = thresholds_all
    weights["penalties"] = penalties_all

    penalty_score = 0
    error_param_list = []

    for i, row in weights.iterrows():
        ptype = row["type"]
        param = row["param"]
        # ignore_params = row["ignore"]

        threshold_penalties = pd.DataFrame()
        threshold_penalties["thresholds"] = row["thresholds"]
        threshold_penalties["penalties"] = row["penalties"]
        threshold_penalties = threshold_penalties.sort_values(by="thresholds", ascending=True)
        xp = threshold_penalties["thresholds"].values
        yp = threshold_penalties["penalties"].values

        # Mask for type
        error_param = param_estimates.loc[param_estimates["param_type"] == param]
        x = error_param[ptype].values
        error_param["penalty_score"] = np.interp(x, xp, yp)

        # Ignore omega estimate penalties if KA is fixed to 0
        # This prevents incorrect peanlisation for 0 order absorption
        if (ptype == "estimated_values"):
            # If a value has a fixed value then don't penalise based on value
            m1 = error_param["fix"] == True
            error_param.loc[m1, "penalty_score"] = np.nan

        # Shrinkage penalty update
        if (ptype == "shrinkage") & (param == "omega"):
            # m1 = error_param["fix"] == True

            # Don't peanalise shrinkage for fixed omegas
            error_param.loc[error_param["fix"] == True, "penalty_score"] = np.nan

            # Don't peanalise ignored params
            if isinstance(row["ignore"], list):
                error_param.loc[error_param["name"].isin(row["ignore"]), "penalty_score"] = np.nan

        # Add penalty to total penalty. Don't sum nan values.
        error_param["penalty_type"] = ptype
        penalty_score +=  sum(error_param["penalty_score"].dropna())
        error_param_list.append(error_param)

    df_penalty = pd.concat(error_param_list).reset_index()
    # df_penalty = df_penalty.rename(columns = {"index": "name"})

    # Reformat dataframe
    df_penalty_pivot = (
        df_penalty[["index", "name", "i", "j", "param_type", "penalty_type", "penalty_score"]]
        .pivot(index=["index", "name", "i", "j", "param_type"], columns=["penalty_type"]))
    df_penalty_pivot.columns = ["_".join(a) for a in df_penalty_pivot.columns.to_flat_index()]
    df_penalty_pivot = df_penalty_pivot.reset_index()

    df_penalty = pd.merge(
        df_penalty[
            [
                "param_type", "i", "j", "estimated_values", "estimated_real", 
                "standard_error", "condition_number", "shrinkage", "log", "fix", "relative_error"]],
        df_penalty_pivot,
        on=["i", "j", "param_type"],
        how="left")

    df_penalty = df_penalty.drop_duplicates(["i", "j", "param_type"])

    # Format parameter estimate table
    cols = [
        "index", "name", "fix", "log", "estimated_values", "estimated_real", "standard_error",
        "relative_error", "condition_number", "shrinkage", 'penalty_score_condition_number', 
        'penalty_score_estimated_values','penalty_score_relative_error', "penalty_score_shrinkage"]
    df_penalty = df_penalty[cols]
    # df_penalty = df_penalty.fillna(0)

    return penalty_score, df_penalty


def calc_model_complexity_penalty(params, model_complexity_weights):

    # # Get control
    # control = read_control(run_dir)

    # # Count params
    # out = count_params(control)
    # penalty = out["penalty"]
    # log_params = out["log_params"]

    # Calculate penalty
    penalty_score = 0
    for penalty in model_complexity_weights:
        # param_key = f"{penalty['param']}_{penalty['type']}_params"
        penalty["count"] = params[penalty["name"]]
        penalty["score"] = penalty["count"] * penalty["penalty"]
        penalty_score += penalty["score"]

    return penalty_score

def read_control(run_dir):
    
    path_split = run_dir.split("/")
    iteration = path_split[-2]
    model = path_split[-1]
    file_name = "NM_" + iteration + "_" + model + ".lst"
    # print(file_name)
    
    with open(os.path.join(run_dir, file_name), "r") as f:
        control = f.read()
    
    return control


def count_params(control):
    
    sections = ["$PROBLEM", "$THETA", "$OMEGA", "$SIGMA", "$ESTIMATION"]
    rows = {}
    log_param_log = {}
    fix_param_log = {}
    param_names = {}
    for i in range(len(sections)):
        section = sections[i]
        
        # Get ncomp data 
        if section == "$ESTIMATION":
            pass
        elif section == "$PROBLEM":
            section_str = control[control.find(section): control.find(sections[i + 1])]
            
            # Find ncomp
            ncomp = section_str.split("NCOMP")[1].split("\n")[0].split("=")[1].strip()
            rows["ncomp"] = ncomp

            # Find transit compartments
            rows["ncomp_transit"] = section_str.count("TRANSIT")

        
        # get parameter data 
        else:
            section_str = control[control.find(section): control.find(sections[i + 1])]
            section_list = section_str.split("\n")
            section_list = [x for x in section_list if x != ""]
            section_list = [x for x in section_list if section not in x]

            total_params = 0
            non_fixed_params = 0
            
            # Extract params
            
            # log_param_log = {
            #     "$THETA": [],
            #     "$OMEGA": [],
            #     "$SIGMA": []
            # }
            
            log_param_log[section[1:].lower()] = []
            fix_param_log[section[1:].lower()] = []
            param_names[section[1:].lower()] = []
 
            for x in section_list:
                x_list = x.split(";")
                if any(char.isdigit() for char in x_list[0]):
                    total_params += 1

                    # Create list of params which have been log transformed or fixed
                    log_param_log[section[1:].lower()].append("LOG" in x)
                    fix_param_log[section[1:].lower()].append("FIX" in x)

                    # Log param name
                    if ";" in x: 
                        param_name = x.split(";")[1].strip()
                    else:
                        param_name = section[1:].lower() + "_" + str(total_params)
                    param_names[section[1:].lower()].append(param_name)

                    # Log number of fixed parameters
                    if "FIX" not in x_list[0]:
                        # print("also fix here")
                        non_fixed_params += 1
            
            section = section[1:]
            row = {
                # section + "_str": section_str,
                section.lower() + "_total_params": total_params,
                section.lower() + "_non_fixed_params": non_fixed_params,
                section.lower() + "_fixed_params": total_params - non_fixed_params
            }

            rows.update(row)            
        
    return {
        "params": rows,
        "log_params": log_param_log,
        "fix_params": fix_param_log,
        "param_names": param_names
    }


def extract_parameter_estimates(run_dir):
    """
    Currently setup for SAEM / IMP estimation
    """
    
    # Get path to ext and shk files file
    run_dir.split("/")[-2]
    a = run_dir.split("/")[-2]
    b = run_dir.split("/")[-1]
    ext_file_name = f"NM_{a}_{b}.ext"
    ext_path = os.path.join(run_dir, ext_file_name)
    shk_file_name = f"NM_{a}_{b}.shk"
    shk_path = os.path.join(run_dir, shk_file_name)
    
    # Load ext data into list
    with open(ext_path) as f:
        lines = f.readlines()
    # with open(ext_path) as f:
    #     lines = f.readlines()
    
    # Extract data from 2nd ext table
    # TODO update with simpler pandas read
    table2 = False
    lines2 = []
    i = 0
    for l in lines:
        if table2:
            l = l.replace("\n", "")
            # Columns
            if i == 0:
                cols = l
                cols = cols.split(" ")
                cols = [x.strip() for x in cols if x != '']
            # Data
            else:
                l = l.split(" ")
                l = [x.strip() for x in l if x != ""]
                lines2.append(l)
            i += 1
        if "TABLE NO.     2:" in l:
            table2 = True

    
    # Format data if table2 found and check if complete
    if table2:
        ext_out = pd.DataFrame(lines2, columns=cols)
        for col in ext_out.columns:
            ext_out[col] = pd.to_numeric(ext_out[col], errors='coerce')
        
        # Once table2 is complete Iteration -1000000000 records estimated values
        estimated_values_complete = any(ext_out["ITERATION"]==-1000000000)
        standard_error_complete = any(ext_out["ITERATION"]==-1000000001)
        condition_complete = any(ext_out["ITERATION"]==-1000000003)
        table2_complete = all([estimated_values_complete, standard_error_complete, condition_complete])


    else:
        table2_complete = False  

    if table2_complete:  

        # Calculate relative error
        estimated_values = ext_out.loc[ext_out.ITERATION==-1000000000].iloc[0][1:-1].to_frame()
        estimated_values.columns = ["estimated_values"]
        estimated_values["standard_error"] = ext_out.loc[ext_out.ITERATION==-1000000001].iloc[0][1:-1]
        estimated_values["condition_number"] = np.nan
        estimated_values.loc[estimated_values.index == "THETA1", "condition_number"] = ext_out.loc[ext_out.ITERATION==-1000000003].iloc[0, 1]
        # estimated_values["relative_error"] = abs(estimated_values["standard_error"] / estimated_values["estimated_values"])

        # Classify param type
        estimated_values.index = estimated_values.index.astype(str)
        estimated_values["param_type"] = np.nan
        estimated_values.loc[estimated_values.index.str.contains("OMEGA"), "param_type"] = "omega"
        estimated_values.loc[estimated_values.index.str.contains("SIGMA"), "param_type"] = "sigma"
        estimated_values.loc[estimated_values.index.str.contains("THETA"), "param_type"] = "theta"
        
        # Label i, j
        estimated_values["i"] = np.nan
        estimated_values["j"] = np.nan
        
        # e_theta = estimated_values["param"] == "theta"
        m_theta = estimated_values["param_type"] == "theta"
        estimated_values.loc[m_theta, "i"] = list(range(1, int(m_theta.sum() + 1)))
        estimated_values["j"] = estimated_values["i"]
        
        # Omega
        m_omega = estimated_values["param_type"] == "omega"
        omega_list = estimated_values[m_omega].index.str.split("(")
        # print(omega_list)
        omega_list_i = [int(x[1].split(",")[0]) for x in omega_list]
        omega_list_j = [int(x[1].split(",")[1].replace(")", "")) for x in omega_list]
        # print(omega_list_i)
        estimated_values.loc[m_omega, "i"] = omega_list_i
        estimated_values.loc[m_omega, "j"] = omega_list_j
        
        # Sigma
        m_sigma = estimated_values["param_type"] == "sigma"
        sigma_list = estimated_values[m_sigma].index.str.split("(")
        # print(sigma_list)
        sigma_list_i = [int(x[1].split(",")[0]) for x in sigma_list]
        sigma_list_j = [int(x[1].split(",")[1].replace(")", "")) for x in sigma_list]
        # sigma_list_j = [x.replace(")", "") for x in sigma_list_j]
        # print(sigma_list_j)
        estimated_values.loc[m_sigma, "i"] = sigma_list_i
        estimated_values.loc[m_sigma, "j"] = sigma_list_j

        # Drop off axis values
        # NOTE Should consider how to handle model with off axis elements
        estimated_values = estimated_values.loc[estimated_values["i"] == estimated_values["j"]]
        
    else:
        # Table 2 not found so model fit was not completed
        estimated_values = None

    # Read shrinkage data

    shk = pd.read_csv(shk_path, delimiter=r"\s+",skiprows=14)
    # shk = pd.read_csv(shk_path, delimiter=r"\s+",skiprows=1)
    omega_shk = list(shk.loc[shk["TYPE"] == 4].iloc[:, 2:].transpose().iloc[:, 0].values)
    estimated_values["shrinkage"] = np.nan
    estimated_values.loc[estimated_values["param_type"]=="omega", "shrinkage"] = omega_shk

    return estimated_values

def write_json_file(dictionary, file_path):
    json_object = json.dumps(dictionary, indent=4)
    with open(file_path, "w") as outfile:
            outfile.write(json_object)


if __name__ == '__main__':
    print("Start")

    # Setup logging
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    loglevel = 2
    logging.basicConfig(level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S")

    # Run penalty function

    # 'Best' model from search
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/ribo/4/4_6n5/temp/FND03/21"

    # Expert model from search
    # Table 2 available and finished
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/cami/2/19_n1/temp/FND01/16"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/cami/3/8_n1/temp/1/38"

    # Table 2 not available
    # run_dir = '/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/cami/3/8_n1/temp/1/05'

    # Table 2 available but not finished
    # run_dir = '/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/cami/3/8_n1/temp/1/12']


    # Table 2 available,estimated values there but no errors
    # run_dir = '/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/cami/3/8_n1/temp/FNS051/121'
    
    # Example with weird errors
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/ola/1/5/n4/temp/FND04/17"
    
    
    # Why won't the new file I need be saved!
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/tagrisso/1/5/n4/temp/FNS040/199"

    # Example where final fitness doesn't seem to match interpretation
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/tagrisso/1/5/n4/temp/FNS040/199"

    # Example which didn't work in the notebook
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/ola/1/8/n0/temp/FND09/19"

    # Shrinkage example
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/tagrisso/1/12/n0/temp/1/35"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/tagrisso/1/12/n0/temp/1/07"

    # Busted add error example
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/ola/1/12/n0/temp/FND06/21"

    # Why is Tagrisso not working?
    # run_dir  = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/tagrisso/1/13/n1/temp/1/01"


    # # Busted looking Evu run
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/evu/1/7/n2/temp/FND02/38"

    # # Busted evu run
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/az_synthetic_data/evu/1/9/n0/temp/1/10"

    #  Testing pyd2
    # run_dir = '/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/poppk/pyd2_test/ribo1_test/temp/1/1'
    # run_dir = "/home/kfdw240/code/ida/autopk/a_test_search/tagrisso/expm/3/n0/temp/1/4"
    # run_dir =  "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/cami/6/2/n0/temp/FND01/02_full"

    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/data/mona/1/3iv/n0/output/ex3"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/data/mona/1/3iv/n0/output/ex1"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/data/mona/1/3iv/n0/output/ex6"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/syn_batch/iv/simple_2/03/n0/temp/0/3/ex2"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/syn_batch/iv/simple_2_2/03/n2/temp/0/3/ex1"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/syn_batch/iv/simple_2_2/03/n2/temp/0/3/ex2"

    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/syn_batch/iv/simple_2_2b/03/n2/temp/0/3"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/syn_batch/ivex/simple_1_1/01/n0/temp/0/2/ex1"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/syn_batch/ivex/simple_1_1/01/n0/temp/0/2/ex3"
    # run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/syn_batch/ivex/simple_1_1/01/n0/temp/0/1/ex4"
    
    # run_dir = "/home/kfdw240/code/ida/autopk/reports/mona/1/3ivb/full_data/1"
    run_dir = "/projects/qcp/QCP_MODELING/OTHER/autoPK/automatization_popPK/data/tagrisso/expm/4/n0/temp/FNS01/03/ex1"
    
    print("RUN DIR:", run_dir)
    
    out = post_process(run_dir)

    print("Post_process output")
    print(out)
