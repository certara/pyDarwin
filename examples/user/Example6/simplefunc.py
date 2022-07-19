import csv
import re
import math
from os.path import exists


def post_process():

    if not exists("ORG.DAT") or not exists("SIM.DAT"):
        return([0.0, ' '])
    hash_map_org = {}
    with open("ORG.DAT") as fp:
        next(fp)
        csv_reader = csv.DictReader(fp, skipinitialspace=True, delimiter = " ")
        for row in csv_reader:
            if float(row["EVID"]) == 0 and float(row["TIME"]) <= 24:
                if row["ID"] not in hash_map_org or math.log(float(row["DV"])) > hash_map_org[row["ID"]]:
                    hash_map_org[row["ID"]] = math.log(float(row["DV"]))
        
    obs_geomean = math.exp(sum(hash_map_org.values()) / len(hash_map_org))

    hash_map_sim = {}
    with open("SIM.DAT") as fp:
        next(fp)
        csv_reader = csv.DictReader(fp, skipinitialspace=True, delimiter = " ")
        for row in csv_reader:
            if float(row["EVID"]) == 0 and float(row["TIME"]) <= 24:
                if row["ID"] not in hash_map_sim or math.log(float(row["IOBS"])) > hash_map_sim[row["ID"]]:
                    hash_map_sim[row["ID"]] = math.log(float(row["IOBS"]))
 
    sim_geomean = math.exp(sum(hash_map_sim.values()) / len(hash_map_sim))
    penalty = 4*abs((obs_geomean-sim_geomean)/obs_geomean)*100 

    text = "Observed day 1 Cmax geomean = {} simulated day 1 Cmax geo mean = {}".format(round(obs_geomean, 1) , round(sim_geomean,1))

    return([penalty, text])