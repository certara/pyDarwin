import numpy as np
import pandas as pd
import math
#import abm
import io
import os
import random
import json
import warnings
#from IPython.utils import io
import statistics
#import time
from statsmodels.stats.contingency_tables import mcnemar


# import runMonteCarlo
# import get_phenotype


def get_phenotype(run_dir: str):
    """
    reads .mod file, converts to json -> study parameters

    Args:
       run_dir: directory of .mod file

    Returns:
       dictionary of parameters
    Raises:
        ValueError: If length or width are negative.
    """
    all_entries = os.listdir(run_dir)
    files_only = [entry for entry in all_entries if os.path.isfile(os.path.join(run_dir, entry))]
    mod_files = [file for file in files_only if file.endswith(".mod")]
    modfile = os.path.join(run_dir, mod_files[0])
    with open(modfile, "r") as f:
        txt = f.read()  # text content of .mode file, has ;;; comments tacked on, need to remove
        txt = txt.split("\n")
    for index, item in enumerate(txt):
        if item.startswith(';'):
            txt[index] = ""
    # convert back to str
    txt = "\n".join(txt)
    parms = json.loads(txt)
    return parms


def runMonteCarlo(parms_means: np.array, cov_normal: np.array, omega: np.array,
                  between_occ_var: np.array, dose: float, dose_times: np.array,  # Simulations: pd.DataFrame,
                  #  Doses: pd.DataFrame,
                  nSamples: int, nSubs: int):
    """
    performs Monte Carlo simulation of nSamples studies, nsamples studies, with nsubs each

    Args:
        parms_means (np.array): Model parameters means, central volume, peripheral volume toxicity beta, efficacy beta
        cov_normal (np.array): covariance matrix of parameters
        Simulations (pd.DataFrame): abm simulation object
        Doses (pd.DataFrame) : abm doses object
        nSamples (integer): number of Monte Carlo study samples
        nSub (integer): number of subjects per study.

    Returns:
         outcomes:
            placeboEffect: fraction effective in placebo arm
            activeEffect: fraction effective in active arm
            type2Error: fraction that fails chi square @ < 0.05
            meanToxFraction: fraction of active with toxicity
    Raises:
        ValueError: If length or width are negative.
    """
    MCResults = {'this_sample': [], 'this_sub': [], 'PlaceboEffective': [], 'PlaceboEffective': [],
                 'PlaceboEffective': [], 'PlaceboEffective': []}

    df = pd.DataFrame(MCResults)

    # add between occasion varibaility
    allOutcomes = pd.DataFrame(columns=['sampleNum',
                                        'placeboFractionEffective',
                                        'placeboFractionToxic',
                                        'activeFractionEffective',
                                        'activeFractionToxic',
                                        'type2Error'])

    SimulationsActive = {'dose_mpk': [dose]}  # 2 simulations, placebo and active
    SimulationsActive = pd.DataFrame(SimulationsActive)
    DosesActive = {'dose_mpk': [dose], \
                   'route': ['IV_mpk'],
                   'amounts': [dose],
                   'amount_unit': ['mg/kg'],
                   'times': [dose_times],
                   'time_unit': ['d']
                   }
    DosesActive = pd.DataFrame(DosesActive)
    # placebo dose is 0, Cmax is 0, RO is 0
    # sys.stdout below result in crash return
    # sys.stdout = open(os.devnull, "w")
    # original_stderr = sys.stderr()
    try:
        # sys.stderr = open(os.devnull, "w")
        # with below does nothing
        # with io.capture_output():
        # sys.stderr = open('file.txt', 'w')
        study_means = np.random.multivariate_normal(parms_means['means'], cov_normal,
                                                    size=nSamples)  # normal distribution
        for this_sample in range(nSamples):
            nPlaceboToxic = 0
            nPlaceboEffective = 0
            nActiveToxic = 0
            nActiveEffective = 0
            etas = np.random.multivariate_normal([0, 0, 0, 0, 0, 0], omega, size=nSubs).T
            pkEtas = etas[range(2)]
            toxEtas = etas[range(2, 4)]
            effectEtas = etas[range(4, 6)]
            # set up all parameters for study
            pkParms = np.zeros((2, nSubs))
            toxParms = np.zeros((2, nSubs))
            effectParms = np.zeros((2, nSubs))
            pkMeans = study_means[this_sample][0:2]  # array length nparms, all pk parameters for a study
            toxMeans = study_means[this_sample][2:4]  # array length nparms, all parameters for toxicity for a study
            effectMeans = study_means[this_sample][4:6]  # array length nparms, all parameters for efficacy for a study
            for i in range(2):
                pkParms[i] = [math.exp(x) * pkMeans[i] for x in pkEtas[i]]  # log normal
                toxParms[i] = [math.exp(x) * toxMeans[i] for x in toxEtas[i]]  # log normal
                effectParms[i] = [math.exp(x) * effectMeans[i] for x in effectEtas[i]]  # log normal
            pkParmsOcc = np.zeros([2])  # n parameters
            for this_sub in range(nSubs):
                # assume placebo has Cmax = 0, but need between occasion for tox and effect
                placebobetween_occasion_etas = np.random.multivariate_normal([0, 0, 0, 0, 0, 0], between_occ_var,
                                                                             size=nSubs).T
                # period 2, active
                activebetween_occasion_etas = np.random.multivariate_normal([0, 0, 0, 0, 0, 0], between_occ_var,
                                                                            size=nSubs).T
                pkBOV = activebetween_occasion_etas[0][0:2]
                # BOV for first periods, all parameters (4)
                # add between occasion variability
                # period 1 parms
                for this_parm in range(2):
                    pkParmsOcc[this_parm] = math.exp(pkBOV[this_parm]) * pkParms[this_parm][this_sub]
                parameters = {'parameter':
                                  ['volume_central', 'volume_peripheral', 'R_per_cell', 'cell_per_ml', 'kon', 'kd_mab',
                                   'el_half', 'R_half', 'Pdist', 'Tdist_hr', 'BW', 'mw'],
                              'unit': ['L', 'L', '1', '1/mL', '1/nM/s', 'nM', 'd', 'min', '1', 'hr', 'kg', 'Da'],
                              'value': [pkParmsOcc[0], pkParmsOcc[1], 10000, 1000000, 0.001,
                                        0.1, 28, 60, 0.12, 12, 70, 150000]
                              }

                parameters = pd.DataFrame(parameters)

                # TresActive = abm.simulate(models="/home/jovyan/pydarwin/RunpyDarwin/OnecompmAB.model",
                #                           # parameters = Tpar,
                #                           parameters=parameters,
                #                           doses=DosesActive,
                #                           simulations=SimulationsActive,
                #                           outputs=['RO1', 'free_drug1_central_conc'],
                #                           times=abm.linspace(0, 21, 2, 'd')).to_pandas(
                #     tall_outputs=True)  # 211 evenly space points over 21 days
                #
                # PKMaxActive = TresActive[TresActive.t == 0]
                # activeCmax = float(PKMaxActive[PKMaxActive.output == 'free_drug1_central_conc']['value'])
                # placeboToxparms = np.zeros([2])
                # activeToxparms = np.zeros([2])
                # # add between occasion variability
                # for i in range(2):
                #     placeboToxparms[i] = math.exp(placebobetween_occasion_etas[i + 2, this_sub]) * toxParms[i, this_sub]
                #     activeToxparms[i] = math.exp(activebetween_occasion_etas[i + 2, this_sub]) * toxParms[i, this_sub]
                # placeboToxic = simLogit(0.0, placeboToxparms[0], placeboToxparms[1])
                # activeToxic = simLogit(float(activeCmax), activeToxparms[0], activeToxparms[1])
                #
                # placeboROmin = 0
                # activeROMin = TresActive[TresActive.t == 1814400.0]
                # activeROMin = float(activeROMin[activeROMin.output == 'RO1']['value'])
                #
                # PlaceboEffective = simLogit(placeboROmin, placeboToxparms[0], placeboToxparms[1])
                # activeEffective = simLogit(activeROMin, activeToxparms[0], activeToxparms[1])
                # nPlaceboToxic = nPlaceboToxic + placeboToxic
                # nPlaceboEffective = nPlaceboEffective + PlaceboEffective
                # nActiveToxic = nActiveToxic + activeToxic
                # nActiveEffective = nActiveEffective + activeEffective
                # Create a 2x2 contingency table for paired data
                # Example: Before vs. After treatment outcomes (Success/Failure)
                # Row 0, Col 0: placebo=Success, treatment=Success
                # Row 0, Col 1: placebo=Success, treatment=Failure
                # Row 1, Col 0: placebo=Failure, treatment=Success
                # Row 1, Col 1: placebo=Failure, treatment=Failure
                PlaceboEffective = 0.5 #simLogit(placeboROmin, placeboToxparms[0], placeboToxparms[1])
                activeEffective = 0.5 #simLogit(activeROMin, activeToxparms[0], activeToxparms[1])
                nPlaceboToxic = 0.5 #nPlaceboToxic + placeboToxic
                nPlaceboEffective = 0.5 #nPlaceboEffective + PlaceboEffective
                nActiveToxic = 0.5 #nActiveToxic + activeToxic
                nActiveEffective = 0.5 #nActiveEffective + activeEffective
               # MCResults = {'this_sample': [], 'this_sub': [], 'PlaceboEffective': [], 'PlaceboEffective': [],
                             'PlaceboEffective': [], 'PlaceboEffective': []}

               # new_row_data = {'Name': 'S', 'Age': 334, 'City': 'c'}
               # df.loc[len(df)] = new_row_data
               # df.to_csv('SimOutput.csv', index=False)
            efficacyChiSqrData = np.array([[nPlaceboEffective, nActiveEffective],
                                           [nSubs - nPlaceboEffective, nSubs - nActiveEffective]])
            efficacyResult = mcnemar(efficacyChiSqrData, exact=False)
            efficacyPval = efficacyResult.pvalue
            efficacySuccess = efficacyPval < 0.05
            studyData = {'sampleNum': [this_sample],
                         'placeboFractionEffective': [nPlaceboEffective / nSubs],
                         'placeboFractionToxic': [nPlaceboToxic / nSubs],
                         'activeFractionEffective': [nActiveEffective / nSubs],
                         'activeFractionToxic': [nActiveToxic / nSubs],
                         'power': [efficacySuccess]}
            studyData = pd.DataFrame(studyData)
            allOutcomes = pd.concat([allOutcomes, studyData])
    finally:
        a = 1
    #        sys.stderr.close()  # close file.txt
    #        sys.stderr = sys.__stderr__

    # sys.stderr = original_stderr
    power = statistics.mean(studyData['power'])
    meanPlaceboEfficacy = statistics.mean(studyData['placeboFractionEffective'])
    meanActiveEfficacy = statistics.mean(studyData['activeFractionEffective'])
    meanTox = statistics.mean(studyData['activeFractionToxic'])
    outcomes = {'placeboEffect': meanPlaceboEfficacy,
                'activeEffect': meanActiveEfficacy,
                'power': power,
                'meanToxFraction': meanTox}
    return outcomes


def simLogit(exposure: float, beta0: float, beta1: float):
    """
    performs simulated logit outcome ~ exposure (concentration or RO)

    Args:
        exposure (float)
        beta0 (float) intercept
        beta1 (float) slope
    Returns:
         outcomes (boolean)

    Raises:
        ValueError: If length or width are negative.
    """
    luck = random.random()
    val = beta0 + beta1 * exposure
    if val > 10:
        val = 10
    if val < -10:
        val = -10
    p = math.exp(val) / (1 + math.exp(val))
    if p > luck:
        outcome = True
    else:
        outcome = False
    return outcome


def post_process2(run):
    """
    performs post processing for pyDarwin. Reads the nm_*.mod, translates into json for study design parameters
    Args:
    run_dir: run directory for pyDarwin model
    Returns:
         objective(s) for optimization
             Cost
             Duration
             Effect size (placebo - active fraction effective))
         constraints: (> 0 is infeasible)
             power > 0.8 (type 2 error < 0.2)
             fraction toxic < 0.1
    Raises:
        ValueError:
    """
    try:
        # logging.getLogger("requests").setLevel(logging.WARNING)
        # logging.getLogger("urllib3").setLevel(logging.WARNING)
        # sys.stdout and sys.stderr causes crash
        # sys.stdout = open(os.devnull, "w")
        # sys.stderr = open(os.devnull, "w")
        # warnings.filterwarnings('ignore')
        # phenotype = get_phenotype.get_phenotype(run_dir)
        phenotype = get_phenotype(run_dir)
        dose = phenotype['Dose']
        nSubs = phenotype['nSubs']
        nSites = phenotype['nSites']
        nSamples = phenotype['nSamples']  # not searched, fixed
        ndoses = 3
        costPerSub = 10000  # dollars
        costPerSite = 10000  # dollars
        acrualRate = 1.0  # subject per week per site
        dose_times = np.linspace(0, 21, ndoses + 1)
        dose_times = dose_times.tolist()  # give one extra @ 21
        parms_means = {
            'parameter': ['volume_central', 'volume_peripheral', 'toxBeta0', 'toxBeta1', 'effectBeta0', 'effectBeta1'],
            'means': [5, 13, -4, 0.001, 0, 0.1]}
        cov_normal = np.array([[0.2, 0.02, 0, 0, 0, 0],
                               [0.02, 0.2, 0, 0, 0, 0],
                               [0, 0, 0.2, 0.02, 0, 0],
                               [0, 0, 0.02, 0.2, 0, 0],
                               [0, 0, 0, 0, 0.04, 0.01],
                               [0, 0, 0, 0, 0.01, 0.4]
                               ])  # uncertainty covariance matrix
        omega = np.array([[0.1, 0.02, 0, 0, 0, 0],
                          [0.02, 0.1, 0, 0, 0, 0],
                          [0, 0, 0.1, 0.02, 0, 0],
                          [0, 0, 0.02, 0.1, 0, 0],
                          [0, 0, 0, 0, 0.1, 0.01],
                          [0, 0, 0, 0, 0.01, 0.1]
                          ])
        between_occ_var = np.array([[0.02, 0.005, 0, 0, 0, 0],
                                    [0.005, 0.02, 0, 0, 0, 0],
                                    [0, 0, 0.02, 0.005, 0, 0],
                                    [0, 0, 0.005, 0.02, 0, 0],
                                    [0, 0, 0, 0, 0.01, 0.001],
                                    [0, 0, 0, 0, 0.001, 0.01]
                                    ])
        #  allOutcomes = runMonteCarlo.runMonteCarlo(parms_means, cov_normal, omega, between_occ_var, dose, dose_times, nSamples, nSubs)
        allOutcomes = runMonteCarlo(parms_means, cov_normal, omega, between_occ_var, dose, dose_times, nSamples, nSubs)
        Cost = nSubs * costPerSub + nSites * costPerSite
        Duration = nSubs / nSites / acrualRate  # weeks
        effectSize = 100 * (allOutcomes['placeboEffect'] - allOutcomes[
            'activeEffect'] / nSubs)  # minimize this (-1) * % increase effective
        if (allOutcomes['power'] >= -1) and (allOutcomes['meanToxFraction'] <= 10):
            Constraint = 0.0
        else:
            Constraint = 1.0
        return [Cost, Duration, effectSize], [
            Constraint]  # , [powerConstraint,  toxConstraint] # constraint > 0 is infeasible solution
    except Exception as e:
        return [99999999, 99999999, 99999999], [1]
