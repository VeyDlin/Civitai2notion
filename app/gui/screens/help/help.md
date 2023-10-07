# Info
Synchronize your Civitai LoRA, checkpoints and embeddings bookmarks and Notion and download them automatically 

`github` - https://github.com/VeyDlin/Civitai2notion

# Using

You need Python 3 version

Just run `start.bat` if you are using Windows or `start.sh ` for Linux, the first installation may take some time

Available utilities:

1. `Import from civitai` - `Import from civitai` - Add all bookmarks from Civitai to the Notion, only those models (LoRA, checkpoints or embeddings) for which you specified the database id in the settings will be added

   At this stage your models has not been downloaded yet, go to your database and edit your entries as desired, for example, sometimes you can add another name/title or change the image, as well as remove duplicates (see point 2)

2. `Download from notion` - Checks the notion database for duplicates, the check takes place by the `File` property, since it will then be used for the names of the files that you download, if duplicates were found, then edit the entries in your notion database, for this you can use the built-in notion search bar to quickly find duplicates by name

   You have the option to use the automatic duplicate conflict resolution setting, in which case the application will simply add a postfix with a digit until the file name becomes unique

   Please note that this utility can also check the hash in the database with already loaded models, this is necessary to fix failed downloads as well as to update models (see point 3)

   Due to the file hash calculation, it may take time if you have a slow hard drive

3. `Update notion database` - Check all models for new versions in Civitai, if new versions of models are found, the application will update the entries in the Notion database

   The action updates the fields `Trigger Words`, `Hash` and `Version`in the Notion database but does not download files

   To update the files you need to run the `Download from notion` utility and select `Download with hash check` 

   This action will start checking the hash and loading models while outdated models will be updated due to a hash mismatch

4. `Make all` Runs in turn `Import from civitai` -> `Update notion database` -> `Download from notion`

# Notion Config

### API Key

1) Go to the `integrations` (https://www.notion.so/my-integrations) and create a new integration

2) In the `Capabilities` menu set all permissions

3) Copy the API key and write it to `Settings` - `Tokens` - `Notion token`

### Database

1) Create a new notion database and name it whatever you want. Use the following properties:

   `Name` - `Type`: `Text` 

   `URL` - `Type`: `URL` 

   `File` - `Type`: `Text` 

   `Trigger Words` - `Type`: `Text` 

   `Tags` - `Type`: `Multi-select`

   `SD` - `Type`: `Select` 

   `Version` - `Type`: `Text` 

   `Model ID` - `Type`: `Text` 
   
   `Hash` - `Type`: `Text` 

2) Create a new database in the notion

3) Create a connection for your database so that the script can create records, to do this, select `...` from the top right and click `Add connections`, select your integration

4) Copy the `Database ID` while you are on the database page and write it to `Settings` - `LoRA settings` - `Notion database id`
    `Database ID` can be found in the browser line

  ```
  https://www.notion.so/myworkspace/a8aec43384f447ed84390e8e42c2e089?v=...
                                    |--------- Database ID --------|
  ```

5) Add at least one path to the folder to save in  `Settings` - `LoRA settings` - `Path to save for 1.x versions` or `Settings` - `LoRA settings` - `Path to save for SDXL versions`. You don't have to do this and then the app will only be able to import your bookmarks, but not download them

6) Repeat steps 2 - 5 in order to create a database for embeddings (`Settings` - `Notion` - `Notion database id for embeddings`) and checkpoints (`Settings` - `Notion` - `Notion database id checkpoints`). You can skip this step, then the program will simply skip processing these categories

# Civitai Config

### API Key

1) Go to the `Account Settings` (https://civitai.com/user/account) and create a new  `API Key`

2) Copy the API key and write it to `Settings` - `Tokens` - `Civit AI token`