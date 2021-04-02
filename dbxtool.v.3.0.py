import base64
import PySimpleGUI as sg
from compare import Compare
from datetime import datetime
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt

sg.theme('DefaultNoMoreNagging')

def draw_plot(categories, datalist, env1, env2):
  
    fig, ax = plt.subplots(figsize=(12, 8))
    width = 0.75
    ind = np.arange(len(categories))
    ax.barh(ind, datalist, width, color="#040085")
    ax.set_yticks(ind+width/10)
    ax.set_yticklabels(categories, rotation= 30, fontsize= 'small', minor=False)
    plt.title('KPI Errors Generated Between {} and {}'.format(env1, env2))
    plt.xlabel('Mismatches')
    plt.ylabel('KPI/API')  
    plt.show(block=False)

environments = ['DEV', 'QA', 'UAT', 'PROD']#You can add new environments here

menuoptions =[
    [
        sg.Text("Environment 1: "),
        sg.InputCombo(environments, size=(10, 1), enable_events=True, key='combo1', default_value="DEV")
    ],
    [
        sg.Text("Environment 2: "),
        sg.InputCombo(environments, size=(10, 1), enable_events=True, key='combo2', default_value="PROD")
    ],
    [
        sg.Text("    "),
        sg.Radio("Mismatch Percentage Bar Chart", "RADIO1", default=True, key='type_of_chart')
    ],
    [
        sg.Text("    "),
        sg.Radio("Error Count Bar Chart", "RADIO1", default=False)
    ],
    [
        sg.Text("Input File *xlsx: ", size=(12, 1)),
        sg.Input(key='FileInput', size=(30, 1),), sg.FilesBrowse(target='FileInput', file_types=(("Text Files", "*.xlsx"),))
    ],
    [
        sg.Text("Output Folder: ", size=(12, 1)),
        sg.Input(key='OutputFolder', size=(30, 1),), sg.FolderBrowse(target='OutputFolder')
    ],
    [
        sg.Button("Compare", size=(10, 1),),
        sg.Button('Cancel', key='Cancel', size=(10, 1),)
    ]
   
]
layout = [
    [
        sg.Column(menuoptions)
    ]
]
window = sg.Window("DBX Tool 3.0 ", layout)
window.Finalize()

while True:
    event, values = window.read()
    if event == "Cancel" or event == sg.WIN_CLOSED:
        break
    elif event == "Compare":
        #sg.Print('  ', do_not_reroute_stdout=False) #You can comment this portion if you need debugging
        window['Compare'].update(disabled = True)
        current_date = datetime.today()
        print("Start time: {}".format(current_date))
        print("---------------------------------(´・(oo)・｀)---------------------------------")
        firstenv = values['combo1']
        secondenv = values['combo2']
        inputfile = values['FileInput']
        outfolder = values['OutputFolder']
        typeofChart = values['type_of_chart']
      
        compare = Compare(firstenv, secondenv, inputfile)
        compare.set_output_path(outfolder)
        compare.compare_values()
        if typeofChart:
            kpidata = compare.compute_percentage_errors()
            countList = [x['percentage'] for x in kpidata]
            kpiLabels = [x['kpi'] for x in kpidata]
        else:
            kpidata = compare.getKPI()
            countList = [x['ERROR_COUNT'] for x in kpidata]
            kpiLabels = [x['KPI'] for x in kpidata]

        draw_plot(kpiLabels, countList, firstenv, secondenv)
        finished_time = datetime.today()
        print("---------------------------------(´・(oo)・｀)-------------------------------")
        print("End Time: {}".format(finished_time))
        elapsedtime = finished_time - current_date
        print("Elapsed Time: {}".format(elapsedtime) )
        sg.popup('Comparison Completed','API Comparison completed between {} and {} environments. Please check the results in the specifed output folder.\n\nElapsed time: {} '.format(firstenv, secondenv,finished_time - current_date) )
        window['Compare'].update(disabled = False)
        window['combo1'].update("Dev")
        window['combo2'].update("Prod")
        window['FileInput'].update("")
        window['OutputFolder'].update("")

window.close()