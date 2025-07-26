import os
import re
import uuid
import traceback

import asyncio
import aiofiles
import aiofiles.os

from .Civitai import Civitai, ModelsTypes
from .Notion import Notion
from .Log import Log
from .Config import Config



class Worker:
    civitai = None
    notion = None
    __busy = False
    __civitai_cache = []
    __notion_cache = {}
    __end_work_call = None
    __work_state_freeze = False


    @staticmethod
    def busy():
        return Worker.__busy


    @staticmethod
    def set_end_work_call(end_work_call):
        Worker.__end_work_call = end_work_call



    @staticmethod
    async def ipmport_models_from_favorites():
        if not Worker.__start_work():
            return

        Log.info("App", "Starting ipmport models from Civit AI favorites to notion database")

        ability = Worker.__get_ability_from_config()

        if all(bool(item["database"]) is False for item in ability.values()):
            Log.error("App", "To work need at least one of settings \"notion database id\"")
            Worker.__end_work()
            return


        # Set filters
        filters = Worker.__get_civitai_filters_from_ability(ability, True)
        Worker.civitai.set_filters(filters, favorites = True)


        # Load all civitai data
        try:
            all_civitai_models = await Worker.__load_all_from_civitai()
        except Exception as err:
            Log.exception("App", f"Load models info from Civit AI error", err, traceback.format_exc())
            Worker.__end_work()
            return
    

        # Add to notion
        civitai_filters = { 
            "lora": [ModelsTypes.LORA, ModelsTypes.LoCon], 
            "checkpoint": [ModelsTypes.Checkpoint], 
            "embedding": [ModelsTypes.TextualInversion] 
        }

        for key, val in ability.items():
            if bool(val["database"]):
                await Worker.__add_models_to_notion(all_civitai_models, civitai_filters[key], val["database"], key)
                    
        
        Log.ok("App", f"End ipmport models")

        Worker.__end_work()




    @staticmethod
    async def download_models_from_notion_database(hash_check):
        if not Worker.__start_work():
            return
        
        ability = Worker.__get_ability_from_config()

        if all(item["active"] is False for item in ability.values()):
            Log.error("App", "To work need at least one combination of settings \"Path to save\" and \"notion database id\"")
            Worker.__end_work()
            return


        # Download from notion
        civitai_version = { "v1_x": ["SD 1.4", "SD 1.5"], "sdxl": ["SDXL 0.9", "SDXL 1.0", "Pony", "Illustrious"] }

        for key, val in ability.items():
            if ability[key]["active"]:
                for version in ability[key]["path"]:
                    path = ability[key]["path"][version]
                    database_id = ability[key]["database"]
                    
                    await Worker.__download_models_from_notion(path, database_id, key, civitai_version[version], version, hash_check)

        Log.ok("App", f"End download models")

        Worker.__end_work()



    @staticmethod
    async def update_notion_database():
        if not Worker.__start_work():
            return
        
        ability = Worker.__get_ability_from_config()

        if all(bool(item["database"]) is False for item in ability.values()):
            Log.error("App", "To work need at least one of settings \"notion database id\"")
            Worker.__end_work()
            return
        

        Log.info("App", "Start update notion database")

        # Update from notion
        for key, val in ability.items():
            if bool(val["database"]):
                await Worker.__update_notion_database(val["database"], key)

        Log.ok("App", f"End update models in notion database. Start \"Download from notion\" to update the model local files")

        Worker.__end_work()



    @staticmethod
    async def make_all(hash_check):
        if not Worker.__start_work():
            return
        
        Worker.__work_state_freeze = True

        await Worker.ipmport_models_from_favorites()
        Worker.__clear_cache()

        await Worker.update_notion_database()
        Worker.__clear_cache()

        await Worker.download_models_from_notion_database(hash_check) 
        Worker.__clear_cache()
        
        Worker.__work_state_freeze = False

        Worker.__end_work()



    @staticmethod
    async def __download_models_from_notion(path, database_id, type, filter_version, version, hash_check):
        Log.info("App", f"Starting download from {type} {version} notion database")

        if not await Worker.__check_notion_database_dublicate(database_id, use_cache = True):
            return

        try:
            all_notion_pages = await Worker.__load_all_from_notion(database_id, use_cache = True)
        except Exception as err:
            Log.exception("App", f"Load {type} database from notion error", err, traceback.format_exc())
            return

        download_counter = 0
        for page in all_notion_pages:
            try:
                if not page["properties"]["SD"] in filter_version:
                    continue

                hash = str(page["properties"]["Hash"]).upper()

                local_file = Worker.__file_exists_with_any_extension(path, page["properties"]["File"])
                if local_file:
                    if not hash_check:
                        continue

                    Log.info("App", f"Check hash for {page['properties']['File']}")
                    if await Civitai.sha256(local_file) == hash:
                        Log.ok("App", f"Hash for {page['properties']['File']} - ok")
                        continue
                    else:
                        Log.warning("App", f"Invalid {page['properties']['File']} hash. Restart download")
                        Log.warning("App", f"Delete old file")
                        await aiofiles.os.remove(local_file)


                await Worker.civitai.download_model(page["properties"]["Model ID"], path, page["properties"]["File"], hash)
                download_counter += 1
            except Exception as err:
                Log.exception("App", f"Error model download", err, traceback.format_exc())

        if not download_counter:
            Log.warning("App", "No new models to download")
        else:
            Log.ok("App", f"Download {download_counter} models")



    @staticmethod
    async def __update_notion_database(database_id, type):
        Log.info("App", f"Starting updating {type} notion database")

        if not await Worker.__check_notion_database_dublicate(database_id, use_cache = True):
            return

        try:
            all_notion_pages = await Worker.__load_all_from_notion(database_id, use_cache = True)
        except Exception as err:
            Log.exception("App", f"Load {type} database from notion error", err, traceback.format_exc())
            return
        

        update_counter = 0
        for page in all_notion_pages:
            try:
                model = await Worker.civitai.get_model_data(page["properties"]["Model ID"])

                page_hash = str(page["properties"]["Hash"]).upper()

                model_hash = str(model["SHA256"]).upper()
                trigger_words = ", ".join(model["triggers"]) 
                model_version = model["version"]

                if page_hash == model_hash:
                    Log.info("App", f"The latest version of the model has already been added - {page['properties']['File']} ({page['properties']['Name']})")
                    continue

                Log.warning("App", f"Outdated model found - {page['properties']['File']} ({page['properties']['Name']})")

                await Worker.notion.update_page(page["id"], {
                    "Trigger Words": {"rich_text": [{"text": {"content": trigger_words}}]},
                    "Hash": {"rich_text": [{"text": {"content": model_hash}}]},
                    "Version": {"rich_text": [{"text": {"content": model_version}}]},
                })
                
                Log.ok("App", f"Model updated - {page['properties']['File']} ({page['properties']['Name']})")

                update_counter += 1
            except Exception as err:
                Log.exception("App", f"Error model update in {type} database", err, traceback.format_exc())

        if not update_counter:
            Log.warning("App", f"No models in {type} database to update")
        else:
            Log.ok("App", f"Update {update_counter} models in {type} database")



    @staticmethod
    async def __add_models_to_notion(civitai_models, model_type_filter, database_id, database_type):
        Log.info("App", f"Starting add {database_type} to notion database")

        try:
            all_notion_pages = await Worker.__load_all_from_notion(database_id)
        except Exception as err:
            Log.exception("App", f"Load {database_type} database from notion error", err, traceback.format_exc())
            return

        # Delete models that have already been added to notion and models that do not fit the type
        filtered_models = []
        for model in civitai_models:
            filter = [x for x in all_notion_pages if x["properties"]["Model ID"] == (str(model["id"]))]
            if not filter and model["type"] in model_type_filter:
                filtered_models.append(model)
        
        notion_file_list = [x["properties"]["File"] for x in all_notion_pages] 

        # Add models to notion
        add_counter = 0
        for model in filtered_models:     
            try:
                name = model["name"]
                url = model["url"]
                file_name = model["name"]
                trigger_words = ", ".join(model["triggers"]) 
                sd_version = str(model["base_model"]).replace(",", ".")
                model_version = model["version"]
                model_id = str(model["id"])
                hash = model["SHA256"]

                tags = ",".join(model["tags"]).split(",")
                tags = [t.strip() for t in tags if t.strip()]
                tags = [{"name": t.replace(",", " ")} for t in tags]

                if Config.get(f"{database_type}.add_version_to_file_name").data:
                    file_name += f" {model_version}"
                file_name = Worker.__get_model_clear_name(file_name, database_type)

                if file_name == "":
                    file_name = uuid.uuid4().hex

                if Config.get(f"{database_type}.simple_titles").data:
                    name = Worker.__get_model_clear_name(model["name"], database_type, " ")

                if Config.get(f"{database_type}.resolve_duplicates").data:
                    if file_name in notion_file_list:
                        Log.warning("App", "Starting automatically resolve duplicates conflicts")
                        new_file_name = file_name
                        new_new_file_name_count = 2
                        while new_file_name in notion_file_list:
                            new_file_name = f"{file_name}_{new_new_file_name_count}"
                            new_new_file_name_count += 1
                        Log.ok("App", f"New file name selected - {new_file_name}")
                        file_name = new_file_name


                await Worker.notion.add_page(database_id, {
                    "Name": {"title": [{"text": {"content":name}}]},
                    "URL": {"type": "url", "url": url},
                    "File": {"rich_text": [{"text": {"content": file_name}}]},
                    "Trigger Words": {"rich_text": [{"text": {"content": trigger_words}}]},
                    "Model ID": {"rich_text": [{"text": {"content": model_id}}]},
                    "Hash": {"rich_text": [{"text": {"content": hash}}]},
                    "SD": { "select": { "name": sd_version } },
                    "Version": {"rich_text": [{"text": {"content": model_version}}]},
                    "Tags": { "type": "multi_select", "multi_select": tags }
                }, next(iter(model.get('images', [])), None))
                
                notion_file_list.append(file_name)

                add_counter += 1
                Log.ok("App", f"Add model \"{model['name']}\" to notion database")
            except Exception as err:
                Log.exception("App", f"Add model \"{model['name']}\" (https://civitai.com/models/{model['id']}) to notion error", err, traceback.format_exc())

        if not add_counter:
            Log.warning("App", "No new models to add")
        else:
            Log.ok("App", f"Added {add_counter} models")
        


    @staticmethod
    async def __check_notion_database_dublicate(database_id, use_cache = True):
        Log.info("App", "Check notion database for duplicates by file name")

        try:
            all_notion_pages = await Worker.__load_all_from_notion(database_id, use_cache)
        except Exception as err:
            Log.exception("App", f"Load database from notion error", err, traceback.format_exc())
            return False


        duplicates = []
        for page in all_notion_pages:
            filter = [x for x in all_notion_pages if x["properties"]["File"] == page["properties"]["File"]]
            if len(filter) > 1:
                duplicates.append(page)
                
        unique_duplicates = list(set([x["properties"]["File"] for x in duplicates]))

        if unique_duplicates:
            Log.error("App", "Duplicates found")

            for duplicate in unique_duplicates:
                Log.warning("App", f"File: {duplicate}")

            Log.info("App", "Rename the \"File\" fields in Notion so that they are unique")
            return False
         

        Log.ok("App", "No duplicates found")
        return True



    @staticmethod
    async def __load_all_from_civitai(use_cache = False):
        if use_cache and Worker.__civitai_cache:
            Log.warning("App", "Use Civit AI cache")
            return Worker.__civitai_cache
        
        all_models = await Worker.civitai.get_all(wait_time = 1)
        Worker.__civitai_cache = Worker.__combined_cache(all_models, Worker.__civitai_cache)

        return all_models
    

    
    @staticmethod
    async def __load_all_from_notion(database_id, use_cache = False):
        if use_cache and database_id in Worker.__notion_cache:
            Log.warning("App", "Use notion cache")
            return Worker.__notion_cache[database_id]

        all_pages = await Worker.notion.get_all(database_id)

        if not database_id in Worker.__notion_cache:
            Worker.__notion_cache[database_id] = []
        Worker.__notion_cache[database_id] = Worker.__combined_cache(all_pages, Worker.__notion_cache[database_id])

        return all_pages



    @staticmethod
    def __combined_cache(data, cache):
        combined = {obj["id"]: obj for obj in cache}
        combined.update({obj["id"]: obj for obj in data})
        return list(combined.values())



    @staticmethod
    def __get_ability_from_config():
        ability = {
            "lora":       {"active": False, "database": "", "path": { }},
            "checkpoint": {"active": False, "database": "", "path": { }},
            "embedding":  {"active": False, "database": "", "path": { }}
        }

        for key, val in ability.items():
            if not Config.get(f"{key}.enable").data:
                continue

            if database := Config.get(f"{key}.notion_database").data:
                ability[key]["database"] = database
                
                if data := Config.get(f"{key}.save_path_v1_x").data:
                    ability[key]["path"]["v1_x"] = data

                if data := Config.get(f"{key}.save_path_sdxl").data:
                    ability[key]["path"]["sdxl"] = data

                ability[key]["active"] = bool(ability[key]["path"])
        
        return ability



    @staticmethod
    def __get_model_clear_name(name, model_type, separator = "_"):
        name = name.lower()

        if data := Config.get(f"{model_type}.file_name_clear").data:
            remove = [tag.strip() for tag in data.split(",")]
            name = " ".join([word for word in name.split() if word not in remove])

        name = re.sub(r'[\W_]+', ' ', name)
        name = re.sub(r'[^\x00-\x7f]', ' ', name)
        name = re.sub(r' +', separator, name.strip())
        return name 



    @staticmethod
    def __get_civitai_filters_from_ability(ability, only_import = False):
        filters = []

        id = "database" if only_import else "active"

        if bool(ability["lora"][id]):
            filters.extend([ModelsTypes.LORA, ModelsTypes.LoCon])
            
        if bool(ability["checkpoint"][id]):
            filters.extend([ModelsTypes.Checkpoint])

        if bool(ability["embedding"][id]):
            filters.extend([ModelsTypes.TextualInversion])

        return filters



    @staticmethod
    def __file_exists_with_any_extension(directory, filename):
        for file in os.listdir(directory):
            file_name, file_extension = os.path.splitext(file)
            if file_name == filename:
                return os.path.join(directory, file)
        return False



    @staticmethod
    def __clear_cache():
        Worker.__civitai_cache = []
        Worker.__notion_cache = {}



    @staticmethod
    def __start_work():
        if Worker.__work_state_freeze:
            return True

        if Worker.__busy:
            return False
        
        Worker.__clear_cache()
        Worker.__init_tokens()

        Worker.__busy = True
        return True



    @staticmethod
    def __end_work():
        if Worker.__work_state_freeze:
            return
        
        Worker.__busy = False
        if Worker.__end_work_call:
            Worker.__end_work_call()


    @staticmethod
    def __init_tokens():
        Worker.civitai = Civitai(Config.get("token.civitai").data)
        Worker.notion = Notion(Config.get("token.notion").data)