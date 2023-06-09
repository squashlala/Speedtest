# * Import des modules requis pour l'exécution du programme
import json, csv, subprocess, time, signal, argparse
from datetime import datetime



# * Définition des arguments
parser = argparse.ArgumentParser(description="Programmes effectuant des test de débits toutes les N secondes et enregistrant les résultats dans des fichiers CSV.\nBasé sur iPerf3.",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--interval", type=int, default=150, help="Interval de temps entre chaques test (secondes)")
parser.add_argument("-d", "--duration", type=int, default=30, help="Durée de chaques test (secondes)")
parser.add_argument("-s", "--servers", type=str ,nargs='+', default=["paris.testdebit.info:9240"], help="Serveurs sur lesquels réaliser le test ex : (\"srv1:port1,srv2:port2&...\")")
config = vars(parser.parse_args())




# * Définition des fonctions d'exécution du rogramme
#Fonction de controle des prérequis
def CheckPrerequisites():
    import subprocess
    AppCheck = subprocess.call(['which', 'iperf3'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if AppCheck != 0:
        print('ERREUR : iPerf3 n\'est pas installé.\n\t"apt/dnf install iperf3"')
        exit(1)

#Fonction de gestion de l'appel Ctrl+C
def handler(signum, frame):
    res = input("\nVoulez-vous arrêter le script? y/N :")
    if res == 'y':
        exit(0)

#Définiton de la fonction à appeler si Ctrl+C
signal.signal(signal.SIGINT, handler)



# * Définition des variables
# Définiton des serveurs à utiliser
iperf_srvTempo = config['servers']
iperf_srv = iperf_srvTempo[0].strip().split(",")

#Définiton de la commande à passer avec champs de server dynamique
iperf_cmd = "iperf3 -c %s -p %s -t %d -S 0 -J"

#Définition de l'heure actuelle
current_time = datetime.now().strftime('%d-%m-%Y_%H:%M')

#Définiton du nom générique des CSV contenant les résultats
#Les chanmps dynamiques sont le type de valeur (raw /dyn) et le serveur scanné
csv_fileGen = "%s_%s_"+current_time+".csv"


#Clear de l'interface
subprocess.call("clear")

#Vérification de la présence des applications necessaires
CheckPrerequisites()

# * Initialisation des fichiers CSV
# Initialisation CSV pour chaques serveurs
for current_srv in iperf_srv :
    for speedName in ['speeds_raw','speeds_Mb'] :
        with open(csv_fileGen %(speedName, current_srv), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['time','server','port','sum_sent', 'sum_received','error'])
            writer.writeheader()



# * Définition des fonctions d'exécution
#Fonction de réalisation du test et parsing du résultat
def get_results(current_srv,current_port):

    #Mise en forme finale de la commande iPerf
    iperf_cmdFull = iperf_cmd %(current_srv, current_port, config['duration'])

    #Exécution de la commande iPerf et sauvegarde du résultat dans une variable
    iperf_result = subprocess.run(iperf_cmdFull, shell=True, capture_output=True, text=True)
    iperf_data = json.loads(iperf_result.stdout)
    
    #Si la sortie JSON contient un champs erreur le test n'a pas fonctionné correctement, affichage de l'heure et inscription des vitesses en "-1"
    if 'error' in iperf_data:
        current_time = datetime.now().strftime('%d/%m/%Y - %H:%M')
        speeds_raw = (current_time,current_srv,current_port,0,0,"'%s'" %(iperf_data['error']))
        speeds_Mb = (current_time,current_srv,current_port,0,0,"'%s'" %(iperf_data['error']))

        #Fermeture de la fonction après erreur
        return speeds_raw, speeds_Mb

    # Input date string in the format "Thu, 04 May 2023 17:24:50 GMT"
    date_string = iperf_data['start']['timestamp']['time']

    # Convert to datetime object
    date_obj = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')

    # Format the datetime object to "04/05/2023 - 17:24"
    formatted_date = date_obj.strftime('%d/%m/%Y - %H:%M')

    #Inscription en table des valeurs brutes
    speeds_raw = (formatted_date, current_srv, current_port, iperf_data['end']['sum_received']['bits_per_second'], iperf_data['end']['sum_sent']['bits_per_second'],"")

    #Inscription en table des valeurs en Mb
    speeds_Mb = (speeds_raw[0], speeds_raw[1], speeds_raw[2], round(speeds_raw[3]/pow(1024,2),0), round(speeds_raw[4]/pow(1024,2),0),"")

    #Fermeture de la fonction avec retour des données de vitesse moyennes
    return speeds_raw, speeds_Mb



# * Main
#Boucle infinie exécutant un test toutes les 2min30 (150s)
while True:

    #Pour chaques serveurs éxécution d'un speed test
    for srvCouple in iperf_srv :

        #Mise en forme des champs
        srvPortSplitted = srvCouple.split(":")

        #Appel de la fonction effectuant le test
        speeds_raw, speeds_Mb = get_results(srvPortSplitted[0],srvPortSplitted[1])

        #Affichage des résultats
        print("%s : Speed for %s is:\tD: %dMbps\tU: %dMbps" %(speeds_Mb[0], srvCouple, speeds_Mb[-3], speeds_Mb[-2]))
        if "" != speeds_Mb[-1] :
            print("\tError : %s" %(speeds_Mb[-1]))

        #Pour chaques types de vitesses, inscription des résultats dans un fichier CSV
        for speedFormat in ['speeds_raw','speeds_Mb'] :
            CSV_file = csv_fileGen %(speedFormat, srvCouple)
            with open(CSV_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if speedFormat == 'speeds_raw':
                    newLine = speeds_raw
                elif speedFormat == 'speeds_Mb':
                    newLine = speeds_Mb
                writer.writerow(newLine)
        #Courte pause du programme avant da passer à l'hôte suivant
        time.sleep(2)
    
    print("")
    #Mise en pause du programme pendant N secondes (définit par argument, voir "python [prog] --help")
    time.sleep(config['interval']-2)
