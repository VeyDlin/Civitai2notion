import json
import shutil
import os
import copy



class ConfigProperty():
    def __init__(self, prop_json_data, group_json_data):
        self.id = prop_json_data["id"]
        self.type = prop_json_data["type"]
        self.data = prop_json_data["data"]
        self.title = prop_json_data["title"]
        self.hint = prop_json_data["hint"]
        self.help = prop_json_data["help"]
        self.path = group_json_data["id"]["val"] + '.' + self.id
        




class ConfigPropertyGroup():
    def __init__(self, group_json_data, properties):
        self.id = group_json_data["id"]["val"]
        self.title = group_json_data["id"]["title"]
        self.properties = properties





class Config():
    groups = []
    __groups_temp = []
    __file = None


    @staticmethod
    def init(file, temp_file = None):
        Config.__file = file

        if not os.path.exists(file) and temp_file is not None:
            shutil.copy2(temp_file, file)

        if temp_file is not None:
            Config.__update(file, temp_file)

        Config.load()



    @staticmethod
    def __update(file, temp_file):
        with open(file, 'r') as f:
            file_data = json.load(f)

        with open(temp_file, 'r') as tf:
            temp_file_data = json.load(tf)

        file_data.update(temp_file_data)

        keys_to_delete = [k for k in file_data if k not in temp_file_data]
        for k in keys_to_delete:
            del file_data[k]

        with open(file, 'w') as f:
            json.dump(file_data, f, indent=4)



    @staticmethod
    def get(id):
        (group_id, prop_id) = id.split('.')
        group = next(((x for x in Config.groups if x.id == group_id)), None)
        prop = next(((x for x in group.properties if x.id == prop_id)), None)
        return prop



    @staticmethod
    def load():
        raw_config = Config.json_load()
        for group in raw_config["config"]:
            properties = []
            for prop in group["properties"]:
                properties.append(ConfigProperty(prop, group))
            Config.groups.append(ConfigPropertyGroup(group, properties))

        Config.__groups_temp = copy.deepcopy(Config.groups)



    @staticmethod
    def save():
        config = []

        for group in Config.groups:
            group_json = {
                "id": {"val": group.id, "title": group.title}, 
                "properties": []
            }
            for prop in group.properties:
                group_json["properties"].append(
                    {"id": prop.id, "type": prop.type, "data": prop.data, "title": prop.title, "hint": prop.hint, "help": prop.help}
                )
            config.append(group_json)

        Config.json_save({"config": config})
        Config.__groups_temp = copy.deepcopy(Config.groups)


    @staticmethod
    def reset():
        Config.groups = copy.deepcopy(Config.__groups_temp)



    @staticmethod
    def json_load():
        with open(Config.__file) as f:
            return json.load(f)



    @staticmethod
    def json_save(data):
        with open(Config.__file, "w") as f:
            f.write(json.dumps(data, indent=4))
