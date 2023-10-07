import aiohttp
import aiofiles
import hashlib
import os
import re
from .Log import Log



class ModelsTypes:
    Checkpoint = "Checkpoint"
    TextualInversion = "TextualInversion"
    Hypernetwork = "Hypernetwork"
    AestheticGradient = "AestheticGradient"
    LORA = "LORA"
    LoCon = "LoCon"
    Controlnet = "Controlnet"
    Poses = "Poses"


class ModelsSort:
    HighestRated = "Highest Rated"
    MostDownloaded = "Most Downloaded"
    Newest = "Newest"


class ModelsPeriod:
    AllTime = "AllTime"
    Year = "Year"
    Month = "Month"
    Week = "Week"
    Day = "Day"



class Civitai():
    token = None
    lats_page = 1
    types = []
    favorites=False


    def __init__(self, token):
        self.token = token



    def set_filters(self, types=[], favorites=False):
        self.types = types
        self.favorites = favorites



    async def get_all(self):
        out_list = []
        while True:
            page_data = await self.get_page_and_next()
            if not page_data:
                break
            out_list.extend(page_data)
        return out_list



    async def get_page_and_next(self, separate_model_request = False):
        Log.info("Civit AI", f"Load page {self.lats_page}")

        out_list = []
        models = await self.__get_models_json(favorites=self.favorites, types=self.types, page=self.lats_page)

        Log.ok("Civit AI", f"Page Loaded ({len(models['items'])} models)")
        

        for model in models["items"]:
            try:
                if separate_model_request:
                    out_list.append(await self.get_model_data(model["id"]))
                else:
                    out_list.append(self.__convert_json_model_data(model))
            except Exception as err:
                Log.error("Civit AI", f"Load model info error. Model: https://civitai.com/models/{model['id']}. {err=}")


        self.lats_page += 1

        return out_list


    
    def to_page(self, page):
        self.lats_page = page


    
    async def download_model(self, id, save_dir, name, hash = None):
        model = await self.get_model_data(id)

        Log.info("Civit AI", f"Start download {id} model")
        response = await aiohttp.ClientSession().get(model["download"], params={'token': self.token})
        format =  self.__get_extension_from_response(response)

        if format is None:
            Log.error("Civit AI", f"Download model {id} ({name}). Unable to download - unknown file extension")
            raise Exception(f"Unknown file extension. Headers: {response.headers}")
        
        if name == "":
            Log.error("Civit AI", f"Download model id: {id}. Unable to download - empty file name")
            raise Exception(f"Unknown file extension. Headers: {response.headers}")
        
        file_path = os.path.join(save_dir, f'{name}.{format}')

        f = await aiofiles.open(file_path, mode = "wb")
        async for chunk in response.content.iter_chunked(1024 * 1024):
            await f.write(chunk)
        await f.close()

        # TODO: Check hash

        Log.ok("Civit AI", f"Model {id} ({name}) successfully downloaded")



    async def download_model_from_url(self, url, save_dir, name, hash = None):
        id = re.search("models\/([0-9]+)", url)[1]
        return await self.download_model(id, save_dir, name, hash)

    

    async def get_model_data(self, id):
        Log.info("Civit AI", f"Load model info. Model ID: {id}")
        model = await self.__get_model_json(id)
        Log.ok("Civit AI", f"Model info loaded - {id} ({model['name']})")
        
        return self.__convert_json_model_data(model)
    


    def __convert_json_model_data(self, model):
        return {
            "url": f"https://civitai.com/models/{model['id']}",
            "tags": model["tags"],
            "id": model["id"],
            "type": model["type"],
            "triggers": model["modelVersions"][0]["trainedWords"],
            "download": model["modelVersions"][0]["files"][0]["downloadUrl"],
            "format": model["modelVersions"][0]["files"][0]["metadata"]["format"],
            "name": model["name"],
            "base_model": model["modelVersions"][0]["baseModel"],
            "version": model["modelVersions"][0]["name"],
            "images": [o["url"] for o in model["modelVersions"][0]["images"]],
            "SHA256": model["modelVersions"][0]["files"][0]["hashes"]["SHA256"]
        }



    async def __get_json(self, page, params = []):
        headers = {"Content-type": "application/json"}

        async with aiohttp.ClientSession().get(f'https://civitai.com/api/v1/{page}', params=params, headers=headers) as response:
            json_data = await response.json()

            if "error" in json_data:
                Log.error("Civit AI", f"JSON get error (https://civitai.com/api/v1/{page}). Error info: {json_data['error']}")
                raise Exception()
        
        return json_data



    async def __get_models_json(self, page = 1, types = [ModelsTypes.Checkpoint], sort = ModelsSort.Newest, period = ModelsPeriod.AllTime, query = "", username = "", favorites = False, nsfw = True):
        return await self.__get_json("models", {
            "page": page, 
            "types": types, 
            "sort": sort, 
            "period": period, 
            "query": query, 
            "username": username, 
            "favorites": "true" if favorites else "false", 
            "nsfw": "true" if nsfw else "false",
            "token": self.token
        }) 



    async def __get_model_json(self, id):
        return await self.__get_json(f"models/{id}") 
    


    async def get_model_from_url_json(self, url):
        id = re.search("models\/([0-9]+)", url)[1]
        return await self.__get_model_json(id)
    

    
    def __get_extension_from_response(self, response):
        cd = response.headers.get("content-disposition")
        if not cd:
            return None
        
        filename = re.findall("filename=\"(.+)\"", cd)
        if len(filename) == 0:
            return None
        
        return filename[0].split(".")[-1]
    


    @staticmethod
    async def sha256(filename):
        f = await aiofiles.open(filename, mode = "rb")
        bytes = await f.read()  

        # TODO: make async hash
        sha256 = hashlib.sha256(bytes).hexdigest().upper()
        await f.close()
        return sha256