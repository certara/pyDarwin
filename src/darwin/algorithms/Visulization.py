import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
# import sys

# sys.path.append('../../../../../')


result_save_path = "C:/Users/xli267/pydarwin/MOGA_test4/output/"
file = open("C:/Users/xli267/pydarwin/MOGA_test4/" + "messages.txt", "r")  ## read messages
content = file.read()

gen = content.split('MOGA best genome =')[1]
gen = gen.split('OFV and #')[0]

gen_list = []
for gen_cur in gen.split('\n'):
    gen_cur = gen_cur.replace("[","")
    gen_cur = gen_cur.replace("]","")
    gen_cur = gen_cur.replace(" ","")
    gen_list.append(gen_cur)

gen_list = gen_list[0: -2]


obj = content.split('OFV and # of parameters =')[1]
obj = obj.split('Final output from')[0]
obj = obj.split('\n')
obj = obj[0:-1]  ## [0:-1 or -2?]

obj_list = []
F1_list = []
F2_list = []
for obj_cur in obj:
    obj_cur = obj_cur.replace("[","")
    obj_cur = obj_cur.replace("]","")
    obj_cur = obj_cur.split(' ')
    F1_cur = float(obj_cur[1])
    F2_cur = float(obj_cur[2])
    F1_list.append(F1_cur)
    F2_list.append(F2_cur)
    # obj_cur = obj_cur.replace(" ","")
    # obj_list.append(obj_cur)

# gen_list = gen_list[0: -2]

result_df = pd.read_csv(result_save_path+ 'results' + '.csv')
F1 = result_df['ofv']
F2 = result_df['ntheta']  ##remember the there's a space before the condition number in excel
# F2 = result_df['total number of parameters']
#convergence
sel_attribute = "success"
result_df_sel1 = result_df[result_df[sel_attribute]==False]
F1_success = result_df_sel1['ofv']
F2_success = result_df_sel1['ntheta']
#covariance
sel_attribute = "covariance"
result_df_sel2 = result_df[result_df[sel_attribute]==False]
F1_covariance = result_df_sel2['ofv']
F2_covariance = result_df_sel2['ntheta']
#correlation
sel_attribute = "correlation"
result_df_sel3 = result_df[result_df[sel_attribute]==False]
F1_correlation = result_df_sel3['ofv']
F2_correlation = result_df_sel3['ntheta']

# plt.figure()
# plt.scatter(F1, F2)
# plt.xlim([7500, 10000])
# plt.ylim([0,30])
# plt.show()


# F1_per = []
# F2_per = []
# for ii in result_df.index:
#     cur_modelid = result_df.loc[ii, 'model']
#     if cur_modelid in gen_list:
#         F1_per.append(result_df.loc[ii, 'ofv'])
#         F1_per.append(result_df.loc[ii, 'total number of parameters'])


plt.figure()
plt.scatter(F1_list, F2_list, color = "firebrick", label = "Pareto Front", zorder = 10)
plt.scatter(F1, F2, color = "plum", label = "Model Tested", alpha = 0.1, zorder = 5)
# plt.scatter(F1_success, F2_success, color = "powderblue", label = "Failed Convergence", alpha = 0.5, zorder = 10)
# plt.scatter(F1_covariance, F2_covariance, color = "lightgreen", label = "Failed Covariance", alpha = 0.5, zorder = 10)
plt.scatter(F1_correlation, F2_correlation, color = "wheat", label = "Failed Correlation", alpha = 0.5, zorder = 10)
plt.legend()
plt.xlim([7500, 10000])   # 7500, 10000 for ofv
plt.ylim([0,18])
plt.xlabel("OFV")
plt.ylabel("# of THETA")
plt.show()

# plt.figure()
# plt.scatter(F1_list, F2_list, color = "firebrick", label = "Pareto Front", zorder = 10)
# plt.scatter(F1, F2, color = "plum", label = "Model Tested", alpha = 0.1, zorder = 5)
# plt.scatter(F1_success, F2_success, color = "blue", label = "Failed Convergence", alpha = 0.5, zorder = 15)
# plt.scatter(F1_covariance, F2_covariance, color = "green", label = "Failed Covariance", alpha = 0.5, zorder = 15)
# plt.scatter(F1_correlation, F2_correlation, color = "red", label = "Failed Correlation", alpha = 0.5, zorder = 15)
# plt.legend()
# plt.xlim([8000, 8100])
# plt.ylim([16,23])
# plt.xlabel("OFV")
# plt.ylabel("# of parameters")
# plt.show()