from CivitaiParser import CivitaiParser
from CivitaiClient import ModelsTypes
from notion_client import Client
from BColors import BColors
import json
import re
import os



class Worker:
    config = None
    civitai = None
    notion = None



    def __init__(self, config_path):
        f = open(config_path)
        self.config = json.load(f)
        f.close()

        self.civitai = CivitaiParser(self.config['civitai']['token'])

        self.notion = Client(auth=self.config['notion']['token'])



    def add_all_lora_favorites(self):
        all_lora_notion = self.get_lora_pages()

        self.civitai.set_filters(favorites=True, types=[ModelsTypes.LORA, ModelsTypes.LoCon])
        self.civitai.to_page(1)

        page_counter = 1

        while True:
            print()
            print(f'{BColors.OKGREEN} [LOAD {page_counter} PAGE] {BColors.ENDC}')

            page_counter += 1

            page_data = self.civitai.get_page_and_next()
            if not page_data:
                break



            for model in page_data:
                filter = [x for x in all_lora_notion if x['url'].startswith(model['url'])]
                if filter:
                    print(f'{BColors.WARNING}   [SKIP] {BColors.ENDC} {model["name"]}')
                else:
                    self.add_lora(
                        title=model['simple_name'] if self.config['notion']['simple_name_in_title'] else model['name'],
                        lora_name=model['lora_name'], 
                        url=model['url'], 
                        triggers=model['triggers'], 
                        image_url=model['images'][0]
                    )
                    print(f'{BColors.OKGREEN}   [ADD] {BColors.ENDC} {model["name"]}')

        print()
        print(f'{BColors.OKGREEN} [------------------------ END ------------------------] {BColors.ENDC}')



    def add_lora(self, title, lora_name, url, triggers, image_url):
        properties = {
            'Name': {'title': [{'text': {'content': title}}]},
            'URL': {'type': 'url', 'url': url},
            'Lora': {'rich_text': [{'text': {'content': lora_name}}]},
            'Trigger Words': {'rich_text': [{'text': {'content': triggers}}]},
            'Tags': {
                'type': 'multi_select',
                'multi_select': [{'name': 'BOTCREATE'}]
            }
        }
        image_block_props= {
            'type': 'image',
            'image': {
                'type': 'external',
                'external': {
                    'url': image_url
                }
            }
        }
        
        return self.notion.pages.create(
            parent={'database_id': self.config['notion']['lora_database']}, 
            properties=properties, 
            children=[image_block_props]
        )



    def get_all_pages(self, database_id):
        print(f'{BColors.OKGREEN} [LOAD NOTION DATABASE] {BColors.ENDC}')

        results = []

        query = self.notion.databases.query(database_id=database_id, page_size=100)
        results.extend([o['properties'] for o in query['results']])

        while query['next_cursor']:
            query = self.notion.databases.query(database_id=database_id, start_cursor=query['next_cursor'], page_size=100)
            results.extend([o['properties'] for o in query['results']])


        return results



    def get_lora_pages(self):
        results = []

        pages = self.get_all_pages(self.config['notion']['lora_database'])
        for page in pages:
            results.append({
                'name': ''.join([x['plain_text'] for x in page['Name']['title']]),
                'lora': ''.join([x['plain_text'] for x in page['Lora']['rich_text']]),
                'url': page['URL']['url']
            })

        return results



    def check_lora_database(self):
        all_lora_notion = self.get_lora_pages()

        duplicates = []
        for page in all_lora_notion:
            filter = [x for x in all_lora_notion if x['lora'] == page['lora']]
            if len(filter) > 1:
                duplicates.append(page)
                
        unique_duplicates = list(set([x['lora'] for x in duplicates]))

        if unique_duplicates:
            for duplicate in unique_duplicates:
                print(f'{BColors.WARNING}   [LORA DUPLICATE] {BColors.ENDC} {duplicate}')
        else:
            print(f'{BColors.OKGREEN} [DUPLICATES NOT FOUND] {BColors.ENDC}')

        print(f'{BColors.OKGREEN} [------------------------ END ------------------------] {BColors.ENDC}')

        return {'duplicates': unique_duplicates, 'pages': all_lora_notion}



    def download_lora_database(self):
        check_database = self.check_lora_database()
        if check_database['duplicates']:
            return
        
        print()
        print(f'{BColors.OKGREEN} [DOWNLOAD] {BColors.ENDC}')

        for lora in check_database['pages']:
            try:
                if not self.file_exists_with_any_extension(self.config['save']['lora_dir'], lora["lora"]):

                    id = re.search('models\/([0-9]+)', lora["url"])[1]
                    self.civitai.download_model(id, self.config['save']['lora_dir'], lora["lora"])

                    print(f'{BColors.OKGREEN}   [LOAD] {BColors.ENDC} {lora["lora"]}    |   {lora["url"]}')

            except Exception as err:
                print(f'{BColors.FAIL}   [ERROR] {err=}, {type(err)=} {BColors.ENDC}')
                
        print(f'{BColors.OKGREEN} [------------------------ END ------------------------] {BColors.ENDC}')



    def file_exists_with_any_extension(self, directory, filename):
        for file in os.listdir(directory):
            file_name, file_extension = os.path.splitext(file)
            if file_name == filename:
                return True
        return False





    def check_checkpoint_database(self):
        pass



    def download_checkpoint_database(self):
        pass


