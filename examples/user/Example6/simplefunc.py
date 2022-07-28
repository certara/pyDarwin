import os
import csv
import re
import math


def post_process(run_dir: str):
    org_dat = os.path.join(run_dir, 'ORG.DAT')
    sim_dat = os.path.join(run_dir, 'SIM.DAT')

    if not os.path.exists(org_dat) or not os.path.exists(sim_dat):
        return 0.0, ''

    hash_map_org = {}

    with open(org_dat) as fp:
        next(fp)

        csv_reader = csv.DictReader(fp, skipinitialspace=True, delimiter=" ")

        for row in csv_reader:
            if float(row["EVID"]) == 0 and float(row["TIME"]) <= 24:
                if row["ID"] not in hash_map_org or math.log(abs(float(row["DV"]))) > hash_map_org[row["ID"]]:
                    hash_map_org[row["ID"]] = math.log(abs(float(row["DV"])))

    obs_geo_mean = math.exp(sum(hash_map_org.values()) / len(hash_map_org))

    hash_map_sim = {}

    with open(sim_dat) as fp:
        next(fp)

        csv_reader = csv.DictReader(fp, skipinitialspace=True, delimiter=" ")

        for row in csv_reader:
            if float(row["EVID"]) == 0 and float(row["TIME"]) <= 24:
                if row["ID"] not in hash_map_sim or math.log(abs(float(row["IOBS"]))) > hash_map_sim[row["ID"]]:
                    hash_map_sim[row["ID"]] = math.log(abs(float(row["IOBS"])))

    sim_geo_mean = math.exp(sum(hash_map_sim.values()) / len(hash_map_sim))

    penalty = 4 * abs((obs_geo_mean - sim_geo_mean) / obs_geo_mean) * 100

    text = f"Observed day 1 Cmax geo mean = {round(obs_geo_mean, 1)}," \
           f" simulated day 1 Cmax geo mean = {round(sim_geo_mean, 1)}"

    return penalty, text
