mkdir geo_app
python3 -m venv ./geo_app_env
source ./geo_app_env/bin/activate
cd geo_app
code .

pip3 install pipreqs
pip3 install pip-tools
pip3 freeze > requirements.txt

pip3 install -r requirements.txt



* **connect to GoogleSheet API:**

```# Use credentials to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
print("Ok")
#connects to google sheets API
sa =gspread.service_account('credentials.json',scope)
sh = sa.open("output")

wks = sh.worksheet("Sheet1")```
