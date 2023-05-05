import json, csv, subprocess, time
from datetime import datetime
#FDQDZQD

iperf_srv = ['paris.testdebit.info']
iperf_cmd = "iperf3 -c %s -p 9240 -t 30 -S 0 -J --logfile result.json --forceflush"
current_time = datetime.now().strftime('%d-%m-%Y_%H:%M')
csv_fileGen = "%s_%s_"+current_time+".csv"

# Initialisation CSV
for current_srv in iperf_srv :
    for speedName in ['speeds_raw','speeds_Mb'] :
        with open(csv_fileGen %(speedName, current_srv), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['time','server','sum_sent', 'sum_received'])
            writer.writeheader()

def get_results(current_srv):

    iperf_cmdFull = iperf_cmd %(current_srv)
    subprocess.run(iperf_cmdFull, shell=True)
    

    # Open the iperf3 JSON output file
    with open('result.json') as j:
        iperf_data = json.load(j)
    
    
    if 'error' in iperf_data:
        current_time = datetime.now().strftime('%d/%m/%Y - %H:%M')
        speeds_raw = (current_time,current_srv,-1,-1)
        speeds_Mb = (current_time,current_srv,-1,-1)
        return speeds_raw, speeds_Mb

    # Input date string in the format "Thu, 04 May 2023 17:24:50 GMT"
    date_string = iperf_data['start']['timestamp']['time']

    # Convert to datetime object
    date_obj = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')

    # Format the datetime object to "04/05/2023 - 17:24"
    formatted_date = date_obj.strftime('%d/%m/%Y - %H:%M')

    #Inscription en table des valeurs brutes
    speeds_raw = (formatted_date,current_srv,iperf_data['end']['sum_received']['bytes'],iperf_data['end']['sum_sent']['bytes'])

    #Inscription en table des valeurs en Mb
    speeds_Mb = (speeds_raw[0],speeds_raw[1],round(speeds_raw[2]/pow(1024,2),0),round(speeds_raw[3]/pow(1024,2),0))

    subprocess.run('cat /dev/null > result.json', shell=True)
    return speeds_raw, speeds_Mb

while True:
    for current_srv in iperf_srv :
        speeds_raw, speeds_Mb = get_results(current_srv)
        for speedFormat in ['speeds_raw','speeds_Mb'] :
            CSV_file = csv_fileGen %(speedFormat, current_srv)
            with open(CSV_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if speedFormat == 'speeds_raw':
                    writer.writerow(speeds_raw)
                elif speedFormat == 'speeds_Mb':
                    writer.writerow(speeds_Mb)
    time.sleep(150)
    subprocess.run('cat /dev/null > result.json', shell=True)