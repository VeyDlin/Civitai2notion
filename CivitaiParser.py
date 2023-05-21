from CivitaiClient import CivitaiClient, ModelsTypes, ModelsSort, ModelsPeriod
import re
from BColors import BColors


class CivitaiParser():
    civitai = None
    lats_page = 1
    types = []
    favorites=False

    def __init__(self, token):
        self.civitai = CivitaiClient(token)



    def get_simple_name(self, name):
        name = re.sub('[\W_]+', ' ', name)
        name = re.sub('concept|lora|beta', ' ', name, flags=re.I)
        name = re.sub(r'[^\x00-\x7f]', ' ', name)
        name = re.sub(' +', '_', name.lower().strip())
        return name 



    def get_model_data(self, id):
        model = self.civitai.get_model(id)
        return {
            'url': f'https://civitai.com/models/{id}',
            'tags': ', '.join(model['tags']),
            'triggers': ', '.join(model['modelVersions'][0]['trainedWords']),
            'download': model['modelVersions'][0]['files'][0]['downloadUrl'],
            'download': model['modelVersions'][0]['files'][0]['metadata']['format'],
            'name': model['name'],
            'lora_name': self.get_simple_name(model['name']),
            'simple_name': self.get_simple_name(model['name']).replace('_', ' '),
            'images': [o['url'] for o in model['modelVersions'][0]['images']]
        }



    def set_filters(self, types=[], favorites=False):
        self.types = types
        self.favorites = favorites



    def get_page_and_next(self):
        out_list = []
        models = self.civitai.get_models(favorites=self.favorites, types=self.types, page=self.lats_page)

        for model in models['items']:
            try:
                out_list.append(self.get_model_data(model['id']))
            except Exception as err:
                print(f'{BColors.FAIL}   [ERROR] {err=}, {type(err)=} {BColors.ENDC}')

        self.lats_page += 1

        return out_list


    
    def to_page(self, page):
        self.lats_page = page



    def download_model(self, id, save_dir, name):
        return self.civitai.download_model(id, save_dir, name)
