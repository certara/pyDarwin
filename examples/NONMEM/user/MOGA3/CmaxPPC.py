import os
import csv
import re
import math

from darwin.options import options

crash_val = options.crash_value


def post_process2(run):
    run_dir = run.run_dir
    org_dat = os.path.join(run_dir, 'ORG.DAT')
    sim_dat = os.path.join(run_dir, 'SIM.DAT')

    if not os.path.exists(org_dat) or not os.path.exists(sim_dat):
        return [], []

    hash_map_org = {}

    with open(org_dat) as fp:
        next(fp)

        csv_reader = csv.DictReader(fp, skipinitialspace=True, delimiter=" ")

        for row in csv_reader:
            if float(row["EVID"]) == 0 and float(row["TIME"]) <= 24 and float(row["DV"]) > 0:
                if row["ID"] not in hash_map_org or math.log(float(row["DV"])) > hash_map_org[row["ID"]]:
                    hash_map_org[row["ID"]] = math.log(float(row["DV"]))

    obs_geo_mean = math.exp(sum(hash_map_org.values()) / len(hash_map_org))

    hash_map_sim = {}

    with open(sim_dat) as fp:
        next(fp)

        csv_reader = csv.DictReader(fp, skipinitialspace=True, delimiter=" ")

        for row in csv_reader:
            if float(row["EVID"]) == 0 and float(row["TIME"]) <= 24 and float(row["IOBS"]) > 0:
                if row["ID"] not in hash_map_sim or math.log(float(row["IOBS"])) > hash_map_sim[row["ID"]]:
                    hash_map_sim[row["ID"]] = math.log(float(row["IOBS"]))

    sim_geo_mean = math.exp(sum(hash_map_sim.values()) / len(hash_map_sim))

    penalty = 4 * abs((obs_geo_mean - sim_geo_mean) / obs_geo_mean) * 100

    res = run.result
    nep = res.estimated_omega_num + res.estimated_theta_num + res.estimated_sigma_num

    return [res.ofv, nep, penalty], [res.ofv - crash_val + 1, 1 - nep]
