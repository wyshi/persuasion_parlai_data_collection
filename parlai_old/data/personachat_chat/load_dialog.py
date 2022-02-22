import pickle
import re
import os

PKL_PATH = './dialogs_pkl'
TXT_PATH = './dialogs_txt'
dir = os.listdir(PKL_PATH)

for pkl in dir:
    # change to txt file
    base = os.path.splitext(pkl)[0]
    txt = base + ".txt"
    # for all the complete dialogs, get rid of the last dialog sentence
    # do not get rid of the last line for incomplete dialogs
    if re.match('.*incomplete.pkl', pkl, flags=0):
        f_incomplete = pickle.load(open(PKL_PATH + '/' + pkl, "rb"))
        dialog_incomplete = []
        # copy dialogs
        for d in f_incomplete['dialog']:
          dialog_incomplete.append(str(d))
        # write to file
        fp_incomplete = open(TXT_PATH + '/' + txt, "w")
        fp_incomplete.write('PERSUADER (0): ' + str(f_incomplete['workers'][0]) + ', ' + str(f_incomplete['persuader_donation']) + '\n')
        fp_incomplete.write('PERSUADEE (1): ' + str(f_incomplete['workers'][1]) + ', ' + str(f_incomplete['persuadee_donation']) + '\n\n')
        fp_incomplete.write('Number of turns: ' + str(f_incomplete['n_turn']) + '\n\n')
        for line in dialog_incomplete:
          fp_incomplete.write(line + '\n')
        fp_incomplete.close()
    else:
        f_complete = pickle.load(open(PKL_PATH + '/' + pkl, "rb"))
        dialog_complete = []
        persuader_wc = 0
        persuadee_wc = 0
        # copy dialogs
        for d in f_complete['dialog']:
          dialog_complete.append(str(d))
        # write to file
        dialog_complete = dialog_complete[:-1]
        fp_complete = open(TXT_PATH + '/' + txt, "w")
        fp_complete.write('PERSUADER (0): ' + str(f_complete['workers'][0]) + ', ' + str(f_complete['persuader_donation']) + '\n')
        fp_complete.write('PERSUADEE (1): ' + str(f_complete['workers'][1]) + ', ' + str(f_complete['persuadee_donation']) + '\n\n')
        fp_complete.write('Number of turns: ' + str(f_complete['n_turn']) + '\n\n')
        for line in dialog_complete:
          p = re.match('\(0\,', line)
          if (p): # persuader
            m = re.match('\(0\, \'(.*?)\'\)|\(0\, \"(.*?)\"\)', line)
            if (m.group(1)):
              persuader_wc += len(m.group(1).split())
            else:
              persuader_wc += len(m.group(2).split())
          else: # persuadee
            m = re.match('\(1\, \'(.*?)\'\)|\(1\, \"(.*?)\"\)', line)
            if (m.group(1)):
              persuadee_wc += len(m.group(1).split())
            else:
              persuadee_wc += len(m.group(2).split())
          fp_complete.write(line + '\n')
        fp_complete.write('\n\n')
        fp_complete.write('PERSUADER (0) word count: ' + str(persuader_wc) + '\n')
        fp_complete.write('PERSUADEE (1) word count: ' + str(persuadee_wc) + '\n')
        fp_complete.close()
