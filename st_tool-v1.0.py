 #!/usr/bin/env python3

import subprocess
import getpass
from json import loads
import argparse
from prettytable import PrettyTable as table
import multiprocessing
from nie.db import netarch
import time

def get_ecors_under_ldap(ldap):
    engine = netarch.engine(query={'charset': 'utf8'}, user='phpview')
    query = '''
    select 
        DISTINCT geo.nie_name, 
        geo.nie_login, 
        geo.ecor_number, 
        e.ECOR_NAME, 
        e.ECOR_ID, 
        e.ECOR_TYPE 
    from 
        nie.gator_ecor_owners geo 
        inner join CMN_INT.AK_ECOR e on e.ECOR_NUMBER = geo.ecor_number 
        inner join CMN_INT.AK_REGION r on e.ECOR_ID = r.ECOR_ID 
    where 
        geo.nie_login = '{ldap}' 
        and e.STATUS = 'Live'
    '''.format(ldap=ldap)

    result = engine.execute(query)
    result = result.fetchall()
    return result


def get_user(cmd,counter,size):
    try:
        out = subprocess.getoutput(cmd)
        printProgressBar(counter,size)
        return out
    except:
        pass


def get_ecors(lst):
    return [item[3] for item in lst]


def get_ecors_cmd(cmd, ecors):
    return [cmd + ecor for ecor in ecors]


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
   
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()




if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='This is for region suspension')

    parser.add_argument(

        'suspension_type',
        choices=['region', 'region_v6', 'machine'],
        type=str,
        help='st_tool.py region -> region level suspension\n st_tool.py machine -> machine level suspension'
    )

    ARGS = parser.parse_args()
    cmd = "suspendtell -a "
    ecors = get_ecors(get_ecors_under_ldap(getpass.getuser()))
    ecors_cmd = get_ecors_cmd(cmd, ecors)

    # using spawn rather than fork
    multiprocessing.set_start_method('spawn')

    #table = PrettyTable()
    #table.field_names = (['Ecorname', 'target', 'network', 'target_type', 'ticket', 'reason'])
    #print("Code is running background.. lets wait for a moment to get output")
    print("checking the suspensions under",getpass.getuser().upper(),"accounts",'\n')
    myTable = table(['EcorName','Target','Network','Target_type','Ticket','Reason'])
    
    size = len(ecors)
    printProgressBar(0,size)
    items = list(range(1+size))
    lst = [size] * size
    
    start_time=time.time()
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    cmd_runs = pool.starmap(
        get_user,
        zip(ecors_cmd, items, lst)

    )

    pool.close()
    pool.join()
    end_time=time.time()

    for ecor, cmd_run in zip(ecors, cmd_runs):
        

        if 'Warning:' in cmd_run:
            continue

        else:
            for row in loads(cmd_run)['matches']:

                if ARGS.suspension_type == row['target_type']:

                    myTable.add_row(
                        [ecor, row['target'], row['network_name'], row['target_type'], row['ticket'], row['reason']])
    print()
    print(myTable)
    print("Time Elapse:",round(end_time-start_time),'Secs..') 
