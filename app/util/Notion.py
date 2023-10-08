import asyncio

from notion_client import AsyncClient

from .Log import Log



class Notion:
    def __init__(self, token):
        self.notion = AsyncClient(auth=token)



    async def get_all(self, database_id):
        pages = await self.__get_all_raw(database_id)

        results = []

        for page in pages:
            properties = {}
            for key, value in page["properties"].items():
                type = value["type"]
                if type == "title":
                    properties[key] = "".join([x["plain_text"] for x in value["title"]])
                if type == "rich_text":
                    properties[key] = "".join([x["plain_text"] for x in value["rich_text"]])
                if type == "multi_select":
                    properties[key] = [x["name"] for x in value["multi_select"]]
                if type == "select":
                    properties[key] = value["select"]["name"] if value["select"] else ""
                if type == "url":
                    properties[key] = value["url"]

            results.append({ "id": page["id"], "properties": properties })

        return results



    async def add_page(self, database_id, properties, image_url = None):
        image_block_props= {
            "type": "image",
            "image": { "type": "external", "external": { "url": image_url } }
        }
        query = await self.__query_retries(lambda: self.notion.pages.create(
            parent = { "database_id": database_id }, 
            properties = properties, 
            children = [image_block_props] if image_url else None
        ))
        return query



    async def update_page(self, page_id, properties):
        query = await self.__query_retries(lambda: self.notion.pages.update(
             page_id, 
             properties = properties
        ))
        return query



    async def update_databases(self, database_id, properties):
        query = await self.__query_retries(lambda: self.notion.databases.update(
             database_id, 
             properties = properties
        ))
        return query
    
  

    async def __get_all_raw(self, database_id):
        page_step = 100
        results = []

        Log.info("notion", f"Load {page_step} pages")
        query = await self.__query_retries(lambda: self.notion.databases.query(database_id=database_id, page_size=page_step))

        results.extend([o for o in query["results"]])
        Log.ok("notion", f"Loaded")

        while query["next_cursor"]:
            Log.info("notion", f"Load {page_step} pages")
            query = await self.__query_retries(lambda: self.notion.databases.query(database_id=database_id, start_cursor=query["next_cursor"], page_size=page_step))

            results.extend([o for o in query["results"]])
            Log.ok("notion", f"Loaded")
            
        return results



    async def __query_retries(self, query_call, wait_time = 1, max_retries = 10):
        retries = 0
        while retries < max_retries:
            try:
                data = await query_call()
                return data
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    Log.warning("notion", f"{e}. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    Log.error("notion", "Max retries reached")
                    raise Exception(e)
