from Worker import Worker
from BColors import BColors
import os



worker = Worker('config.json')



def select_scenario():
    os.system('cls')

    print('[1] Add LoRA from favorites')
    print('[2] Check LoRA database')
    print('[3] Download LoRA from database')
    print()

    print('Select a scenario: ', end='')
    scenario = input()

    os.system('cls')

    if scenario == '1':
        worker.add_all_lora_favorites()

    if scenario == '2':
        worker.check_lora_database()

    if scenario == '3':
        worker.download_lora_database()

    



while True:
    select_scenario()

    print()
    input('Press any key to select a scenario')
