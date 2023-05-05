# * Import des modules requis pour l'exécution du programme
import csv, subprocess, time, signal, argparse
from datetime import datetime



# * Définition des arguments
parser = argparse.ArgumentParser(description="Programmes effectuant des test de débits toutes les N secondes et enregistrant les résultats dans des fichiers CSV.\nBasé sur iPerf3.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--interval", type=int, default=150, help="Interval de temps entre chaques test (secondes)")
config = vars(parser.parse_args())



# * Définition de la gestion d'appuis surCtrl+C pour finir la boucle
#Focntion de gestion de l'appel Ctrl+C
def handler(signum, frame):
    res = input("Voulez-vous arrêter le script? y/n ")
    if res == 'y':
        exit(1)

#Définiton de la fonction à appeler si Ctrl+C
signal.signal(signal.SIGINT, handler)



# * Définition des variables
# Définiton des serveurs à utiliser
iperf_srv = ['paris.testdebit.info']

#Définiton de la commande à passer avec champs de server dynamique
iperf_cmd = "iperf3 -c %s -p 9240 -t 30 -S 0 -J"

#Définition de l'heure actuelle
current_time = datetime.now().strftime('%d-%m-%Y_%H:%M')

#Définiton du nom générique des CSV contenant les résultats
#Les chanmps dynamiques sont le type de valeur (raw /dyn) et le serveur scanné
csv_fileGen = "%s_%s_"+current_time+".csv"




# ! Inutile si sauvegarde en var OK
# * Purge du fichier JSON et clear du terminal
# subprocess.run('cat /dev/null > result.json; clear', shell=True)



# * Initialisation des fichiers CSV
# Initialisation CSV pour chaques serveurs
for current_srv in iperf_srv :
    for speedName in ['speeds_raw','speeds_Mb'] :
        with open(csv_fileGen %(speedName, current_srv), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['time','server','sum_sent', 'sum_received'])
            writer.writeheader()



# * Définition des fonctions d'exécution
#Fonction de réalisation du test et parsing du résultat
def get_results(current_srv):

    #Mise en forme finale de la commande iPerf
    iperf_cmdFull = iperf_cmd %(current_srv)

    # ! A tester
    #Exécution de la commande iPerf et sauvegarde du résultat dans une variable
    iperf_data = subprocess.run(iperf_cmdFull, shell=True)
    

    # ! Inutile si sauvegarde en var OK
    # Open the iperf3 JSON output file
    # with open('result.json') as j:
    #     iperf_data = json.load(j)
    
    #Si la sortie JSON contient un champs erreur le test n'a pas fonctionné correctement, affichage de l'heure et inscription des vitesses en "-1"
    if 'error' in iperf_data:
        current_time = datetime.now().strftime('%d/%m/%Y - %H:%M')
        speeds_raw = (current_time,current_srv,-1,-1)
        speeds_Mb = (current_time,current_srv,-1,-1)

        #Fermeture de la fonction après erreur
        return speeds_raw, speeds_Mb

    # Input date string in the format "Thu, 04 May 2023 17:24:50 GMT"
    date_string = iperf_data['start']['timestamp']['time']

    # Convert to datetime object
    date_obj = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')

    # Format the datetime object to "04/05/2023 - 17:24"
    formatted_date = date_obj.strftime('%d/%m/%Y - %H:%M')

    #Inscription en table des valeurs brutes
    speeds_raw = (formatted_date, current_srv, iperf_data['end']['sum_received']['bytes'], iperf_data['end']['sum_sent']['bytes'])

    #Inscription en table des valeurs en Mb
    speeds_Mb = (speeds_raw[0], speeds_raw[1], round(speeds_raw[2]/pow(1024,2),0), round(speeds_raw[3]/pow(1024,2),0))

    # ! Inutile si sauvegarde en var OK
    #Purge du fichier de résultats
    # subprocess.run('cat /dev/null > result.json', shell=True)

    #Fermeture de la fonction avec retour des données de vitesse moyennes
    return speeds_raw, speeds_Mb



# * Main
#Boucle infinie exécutant un test toutes les 2min30 (150s)
while True:

    #Pour chaques serveurs éxécution d'un speed test
    for current_srv in iperf_srv :

        #Appel de la fonction effectuant le test
        speeds_raw, speeds_Mb = get_results(current_srv)

        #Affichage des résultats
        print('Current speed for %s is:\tD: %dMbps\tU: %dMbps' %(current_srv, speeds_Mb[-2], speeds_Mb[-1]))

        #Pour chaques types de vitesses, inscription des résultats dans un fichier CSV
        for speedFormat in ['speeds_raw','speeds_Mb'] :
            CSV_file = csv_fileGen %(speedFormat, current_srv)
            with open(CSV_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if speedFormat == 'speeds_raw':
                    writer.writerow(speeds_raw)
                elif speedFormat == 'speeds_Mb':
                    writer.writerow(speeds_Mb)
    
    
    #Mise en pause du programme pendant N secondes (définit par argument, voir "python [prog] --help")
    time.sleep(config['interval'])
