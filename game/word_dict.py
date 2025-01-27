import os

def w_dict():
    retdict = []
    # load dict.txt as d_file
    with open(str(os.path.dirname(__file__))+'/dict.txt', 'r') as d_file:
        for line in d_file:
            retdict.append(line.strip())
    return retdict