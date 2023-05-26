import requests
import shutil
import os



class ModelsTypes:
    Checkpoint = 'Checkpoint'
    TextualInversion = 'TextualInversion'
    Hypernetwork = 'Hypernetwork'
    AestheticGradient = 'AestheticGradient'
    LORA = 'LORA'
    LoCon = 'LoCon'
    Controlnet = 'Controlnet'
    Poses = 'Poses'


class ModelsSort:
    HighestRated = 'Highest Rated'
    MostDownloaded = 'Most Downloaded'
    Newest = 'Newest'


class ModelsPeriod:
    AllTime = 'AllTime'
    Year = 'Year'
    Month = 'Month'
    Week = 'Week'
    Day = 'Day'


class CivitaiClient():
    session = requests.Session()
    token = None



    def __init__(self, token):
        self.token = token



    def get_json(self, page, params = []):
        headers = {'Content-type': 'application/json'}

        data = self.session.get(f'https://civitai.com/api/v1/{page}', headers=headers, params=params) 
        json_data = data.json()

        if 'error' in json_data:
            raise Exception(json_data['error'])
        
        return json_data



    def get_models(self, page = 1, types = [ModelsTypes.Checkpoint], sort = ModelsSort.Newest, period = ModelsPeriod.AllTime, query = '', username = '', favorites = False, nsfw = True):
        return self.get_json('models', {
            'page':page, 
            'types':types, 
            'sort':sort, 
            'period':period, 
            'query':query, 
            'username':username, 
            'favorites':'true' if favorites else 'false', 
            'nsfw':'true' if nsfw else 'false',
            'token':self.token
        }) 



    def get_model(self, id):
        return self.get_json(f'models/{id}') 
    


    def download_model(self, id, save_dir, name):
        model = self.get_model(id)

        download_url =  model['modelVersions'][0]['files'][0]['downloadUrl']
        format =  self.format_convert(model['modelVersions'][0]['files'][0]['metadata']['format'])
                                 
        response = self.session.get(download_url, params={'token':self.token}, stream=True)

        with response as r:
            media_file = os.path.join(save_dir, f'{name}.{format}')
            with open(media_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)



    def format_convert(self, format):
        format = format.lower()

        if format == 'safetensor':
            return 'safetensors'
        
        return format
        