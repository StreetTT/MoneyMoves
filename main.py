from os import getenv
from requests import request
from sys import exit
from json import loads
from datetime import datetime as dt


def URLToDBID(url):
    parts = url.split("/")
    if len(parts) >= 2:
        return parts[-1].split("-")[-1].split("?")[0]
    else:
        print("No URL Detected")
        exit()


def MakeRequest(method, url, message, data=None):
    if data is None:
        res = request(method=method, url=url, headers=HEADERS)
    else:
        res = request(method=method, url=url, json=data, headers=HEADERS)
    print(f"{res.status_code} | {method} | {message}\n")
    if res.status_code != 200:
        print(f"{res.text}\n")
    else:
        return loads(res.text)


LANDINGID = URLToDBID(getenv("landingurl"))
TYPE = ["Income", "Expense"]
NOTIONTOKEN = getenv("notiontoken")
HEADERS = {
    "Authorization": f"Bearer {NOTIONTOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
LandingPageChildren = MakeRequest(
    "GET",
    f"https://api.notion.com/v1/blocks/{LANDINGID}/children",
    "Landing Page Children",
)["results"]
for block in LandingPageChildren:
    if block.get("child_database") == None:
        SettingsPageID = block["id"]
    else:
        if (block.get("child_database")).get("title") == "Transactions":
            TransactionsDBID = block["id"]
SettingsPageChildren = MakeRequest(
    "GET",
    f"https://api.notion.com/v1/blocks/{SettingsPageID}/children",
    "Settings Page Children",
)["results"]
for block in SettingsPageChildren:
    if block.get("type", None) != None:
        AccountDBID = block["id"]
AccountDatabaseData = MakeRequest(
    "POST", f"https://api.notion.com/v1/databases/{AccountDBID}/query", "Accounts"
)["results"]
Accounts = {}
for record in AccountDatabaseData:
    Accounts.update(
        {record["properties"]["Name"]["title"][0]["plain_text"]: record["id"]}
    )

account = -1
while account == -1:
    print("What account is this transaction on?")
    for index, transaction in enumerate(Accounts.keys()):
        print(str(index + 1) + ") " + transaction)
    account = input()
    try:
        account = int(account)
        if account not in list(range(1, len(Accounts.keys()) + 1)):
            account = -1
            print("Pick a valid choice")
    except ValueError:
        account = -1
        print("Pick a valid choice")
account = (list(Accounts.keys()))[account - 1]
expenseType = -1
while expenseType == -1:
    print("What type of transaction is it?")
    for index, type in enumerate(TYPE):
        print(str(index + 1) + ") " + type)
    expenseType = input()
    try:
        expenseType = int(expenseType)
        if expenseType not in list(range(1, len(TYPE) + 1)):
            expenseType = -1
            print("Pick a valid choice")
    except ValueError:
        expenseType = -1
        print("Pick a valid choice")
expenseType = TYPE[expenseType - 1]
amount = -1
while amount < 0:
    print("How much was this transaction?")
    amount = input()
    try:
        amount = float(amount)
        if amount < 0:
            print("Transaction must be more than 0")
    except ValueError:
        amount = -1
        print("Pick a valid choice")
if expenseType == "Expense":
    amount = -amount
print("Sumarise this transaction")
reason = input()
data = {
    "parent": {"type": "database_id", "database_id": TransactionsDBID},
    "properties": {
        "Account": {"type": "relation", "relation": [{"id": Accounts[account]}]},
        "Amount": {"type": "number", "number": amount},
        'Date': {'type': 'date', "date": {"start": (dt.now()).isoformat()}},
        "Name": {
            "type": "title",
            "title": [{"type": "text", "text": {"content": reason}}],
        },
    },
}
MakeRequest("POST", "https://api.notion.com/v1/pages", "New Transaction", data)
