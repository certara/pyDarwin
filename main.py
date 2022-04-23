""""
Sponsor:FDA OGD 
Program:
Programmer’s Name: Mark Sale
Date:13Apr2022
Purpose:
Brief Description:
Platform: Windows
Environment: 
Input:
Output:
Notes:  
ModifiedBy:
    Date: 21 Apr, 2022
    Details: updated the template.printmessage
    Effective
"""
import GlobalVars
import Templater
import logging
import model_code
import time
import sys

import gc

logger = logging.getLogger(__name__)


def run_search(template_file: str, tokens_file: str, options_file: str) -> Templater.model:
    """
    run algorithm selected in options_file, based on template_file and tokens_file
    At the end, write best control and output file to homeDir (specified in options_file) 
    options_file path name should, in general, be absolute, other file names can be absolute path
    or path relative to the homeDir
    function returns the final model object
    """

    try:  # path to tokens/template is relative to homeDir, probably need to give full path to template/tokens??
        model_template = Templater.template(template_file, tokens_file, options_file)
    except Exception as e:
        logger.error(e)
        raise

    GlobalVars.Set_up_Objects()
    genome_length = sum(model_template.gene_length)

    # initialize a trivial model for the global best
    null_code = model_code.model_code([0] * genome_length, "None", model_template.gene_max, model_template.gene_length)
    GlobalVars.BestModel = Templater.model(model_template, null_code, -99, True, -99)
    GlobalVars.BestModel.fitness = model_template.options['crash_value'] + 1
    algorithm = model_template.options['algorithm']

    model_template.printMessage(f"Search start time = {time.asctime()}")

    if algorithm in ["GBRT", "RF", "GP"]:
        import OPT
        final = OPT.run_skopt(model_template)
    elif algorithm == "GA":
        import GA
        final = GA.run_GA(model_template)
    elif algorithm == "EXHAUSTIVE":
        import exhaustive
        final = exhaustive.exhaustive(model_template)
    elif algorithm == "PSO":
        import PSO
        final = PSO.run_pso(model_template)
    else:
        print(f"Algorithm {algorithm} is not available")
        sys.exit()

    model_template.printMessage(f"Number of unique models to best model = {GlobalVars.UniqueModelsToBest}")
    model_template.printMessage(f"Time to best model = {GlobalVars.TimeToBest / 60:0.1f} minutes")

    model_template.printMessage(f"Search end time = {time.asctime()}")
    gc.collect()

    return final


if __name__ == '__main__':
    # best_modelEx = run_search(
    #     "C:/fda/FDA-OGD-ML/examples/example_small_2est_withsim/example_small_2est_withsim_template.txt",
    #     "C:/fda/FDA-OGD-ML/examples/example_small_2est_withsim/example_small_tokens.json",
    #     "C:/fda/FDA-OGD-ML/examples/example_small_2est_withsim/exhaustiveoptions74.json")
    # print(f"#\n#\n# Start GA for example5, at {time.asctime()}")
    # best_modelEx2 = run_search("C:/fda/FDA-OGD-ML/examples/ga/example5_template.txt",
    #                            "C:/fda/FDA-OGD-ML/examples/ga/example5_tokens.json",
    #                            "C:/fda/FDA-OGD-ML/examples/GA/gaoptions.json")
    # # print(f"#\n#\n# Start GP for example5, at {time.asctime()}")
    # best_modelEx3 = run_search("C:/fda/FDA-OGD-ML/examples/GP/example5_template.txt",
    #                            "C:/fda/FDA-OGD-ML/examples/GP/example5_tokens.json",
    #                           "C:/fda/FDA-OGD-ML/examples/GP/GPoptions.json") 
    best_modelEx4 = run_search("C:/fda/FDA-OGD-ML/examples/example5/example5_template.txt",
                               "C:/fda/FDA-OGD-ML/examples/example5/example5_tokens.json",
                               "C:/fda/FDA-OGD-ML/examples/example5/exhaustiveoptions74.json")
    best_modelEx4 = run_search("C:/fda/FDA-OGD-ML/examples/example5/example5_template.txt",
                               "C:/fda/FDA-OGD-ML/examples/example5/example5_tokens.json",
                               "C:/fda/FDA-OGD-ML/examples/example5/exhaustiveoptions74.json")
    # best_modelEx5 = run_search("C:/fda/FDA-OGD-ML/examples/search_omega/example_small_1est_nosim_template.txt",
    #                            "C:/fda/FDA-OGD-ML/examples/search_omega/example_small_tokens.json",
    #                            "C:/fda/FDA-OGD-ML/examples/search_omega/omega_options.json")