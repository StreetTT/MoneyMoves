from os import getenv
from requests import request
from sys import exit
from json import loads
from datetime import datetime as dt


def MakeRequest(method: str, url: str, message: str, data: dict = None):
    if data is None:
        res = request(method=method, url=url, headers=HEADERS)
    else:
        res = request(method=method, url=url, json=data, headers=HEADERS)
    print(f"{res.status_code} | {method} | {message}\n")
    if res.status_code != 200:
        print(f"{res.text}\n")
    else:
        return loads(res.text)


TYPE = ["Income", "Expense"]
NOTIONTOKEN = getenv("notiontoken")
HEADERS = {
    "Authorization": f"Bearer {NOTIONTOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


class MoneyMove:

    def __init__(self, url: str):
        self.__Accounts = []
        self.__URL = self.__NotionURLToID(url)
        self.__RetriveFromNotion()
        self.MainMenu()

    def GetURL(self):
        return self.__URL

    def GetTransactionsDBID(self):
        return self.__TransactionsDBID

    def GetAccount(self, index: int = -1):
        if index != -1:
            return self.__Accounts[index]
        return self.__Accounts

    def AppendAccount(self, account):
        self.__Accounts.append(account)

    def MainMenu(self):
        selection = -1
        print("Welcome to Money Moves!", end=" ")
        while selection == -1:
            print("""Select an Option: 
            1) View Balance
            2) Make Transaction
            3) Quit""")
            selection = input()
            try:
                selection = int(selection)
                if selection not in [1, 2, 3]:
                    selection = -1
                    print("Pick a valid choice")
            except ValueError:
                selection = -1
                print("Pick a valid choice")
            if selection == 1:
                print("Account Balance")
                for account in self.__Accounts:
                    print(str(account))
            elif selection == 2:
                again = "Y"
                while again == "Y":
                    Transaction(self)
                    again = input(
                        "Enter 'Y' to enter another Transaction: ").upper()
            elif selection == 3:
                print("Thank You")
                exit()
            selection = -1

    def __NotionURLToID(self, url: str):
        parts = url.split('/')
        if len(parts) >= 2:
            return parts[-1].split('-')[-1].split('?')[0]
        else:
            print("No URL Entered")
            exit()

    def __RetriveFromNotion(self):
        # Takes the information from notion and parse's it into the classes
        LandingPageChildren = MakeRequest(
            "GET", f"https://api.notion.com/v1/blocks/{self.__URL}/children",
            "Landing Page Children")["results"]
        for block in LandingPageChildren:
            if block.get("child_database") == None:
                SettingsPageID = block["id"]
            else:
                if (block.get("child_database")
                    ).get("title") == "Transactions":
                    self.__TransactionsDBID = block["id"]
        SettingsPageChildren = MakeRequest(
            "GET",
            f"https://api.notion.com/v1/blocks/{SettingsPageID}/children",
            "Settings Page Children")["results"]
        for block in SettingsPageChildren:
            if block.get("type", None) != None:
                AccountDBID = block["id"]
        AccountDatabaseData = MakeRequest(
            "POST", f"https://api.notion.com/v1/databases/{AccountDBID}/query",
            "Accounts")["results"]
        for record in AccountDatabaseData:
            roundUp = record["properties"]["Round Up To"]["relation"]
            if len(roundUp) == 1:
                roundUp = self.__FindAccount(roundUp[0]["id"])
            else:
                roundUp = False
            when = record["properties"]["Tunnel When"]["select"]
            if when == None:
                when = False
            else:
                when = when["name"]
            roundUp = record["properties"]["Round Up To"]["relation"]
            if len(roundUp) == 1:
                roundUp = roundUp[0]["id"]
            else:
                roundUp = False
            to = record["properties"]["Tunnel To"]["relation"]
            if len(to) == 1:
                to = to[0]["id"]
            else:
                to = False
            balance = MakeRequest(
                "Get",
                f'https://api.notion.com/v1/pages/{record["id"]}/properties/{record["properties"]["Total"]["id"]}',
                f'{record["properties"]["Name"]["title"][0]["plain_text"]} Balance'
            )["property_item"]["rollup"]["number"]
            self.AppendAccount(
                Account(record["properties"]["Name"]["title"][0]["plain_text"],
                        record["id"], round(balance, 2), roundUp, when, to))
        for account in self.__Accounts:
            if account.GetRoundUp():
                account._SetRoundUp(self.__FindAccount(account.GetRoundUp()))
            if account.GetTunnel():
                account._SetTunnelTo(self.__FindAccount(account.GetTunnel()["To"]))

    def __FindAccount(self, iD: str):
        for account in self.__Accounts:
            if iD == account.GetID():
                return account


class Account:

    def __init__(self,
                 name: str,
                 iD: str,
                 amount: int,
                 roundUp: bool = False,
                 when: str = False,
                 to: str = False):
        self.__Name = name
        self.__Amount = amount
        self.__ID = iD
        self.__RoundUp = roundUp
        if not (when or to):
            self.__Tunnel = False
        else:
            self.__Tunnel = {"When": when, "To": to}

    def GetName(self):
        return self.__Name

    def GetID(self):
        return self.__ID

    def GetRoundUp(self):
        return self.__RoundUp

    def GetTunnel(self):
        return self.__Tunnel

    def _SetRoundUp(self, roundUp):
        self.__RoundUp = roundUp

    def _SetTunnelTo(self, tunnelTo):
        self.__Tunnel["To"] = tunnelTo

    def GetAmount(self):
        return self.__Amount

    def __str__(self):
        return self.__Name + ": £" + format(self.__Amount, '.2f')

    def ApplyTransaction(self, amount: int):
        self.__Amount += amount


class Transaction:

    def __init__(self, mm: MoneyMove):
        self.__mm = mm
        self.Account = -1
        self.GetAccount()
        self.ExpenseType = -1
        self.GetExpenseType()
        self.RealAmount = -1
        self.GetAmount()
        self.Amount = self.RealAmount
        self.Reason = None
        self.GetReason()
        self.__DetermineType()

    def __DetermineType(self):
        if self.Account.GetRoundUp() and self.ExpenseType == "Expense":
            self.Amount = (int(abs(self.RealAmount)) + 1)
        self.__MakeTransaction()
        if self.Account.GetRoundUp() and self.ExpenseType == "Expense":
            self.__MakeRoundUpTransaction()
        if self.Account.GetTunnel(
        ) and self.ExpenseType == self.Account.GetTunnel()["When"]:
            self.__MakeTunnelTransaction()

    def __MakeTransaction(self):
        data = {
            'parent': {
                'type': 'database_id',
                'database_id': self.__mm.GetTransactionsDBID()
            },
            'properties': {
                'Account': {
                    'type': 'relation',
                    'relation': [{
                        'id': self.Account.GetID()
                    }]
                },
                'Amount': {
                    'type': 'number',
                    'number': -self.Amount
                },
                'Date': {
                    'type': 'date',
                    "date": {
                        "start": dt.today().isoformat()[:10]
                    }
                },
                'Name': {
                    'type': 'title',
                    'title': [{
                        'type': 'text',
                        'text': {
                            'content': self.Reason
                        }
                    }]
                }
            }
        }
        MakeRequest("POST", "https://api.notion.com/v1/pages",
                    "New Transaction", data)
        self.Account.ApplyTransaction(self.Amount)

    def __MakeRoundUpTransaction(self):
        data = {
            'parent': {
                'type': 'database_id',
                'database_id': self.__mm.GetTransactionsDBID()
            },
            'properties': {
                'Account': {
                    'type': 'relation',
                    'relation': [{
                        'id': self.Account.GetRoundUp().GetID()
                    }]
                },
                'Amount': {
                    'type': 'number',
                    'number': self.Amount + self.RealAmount
                },
                'Date': {
                    'type': 'date',
                    "date": {
                        "start": dt.today().isoformat()[:10]
                    }
                },
                'Name': {
                    'type': 'title',
                    'title': [{
                        'type': 'text',
                        'text': {
                            'content': self.Reason
                        }
                    }]
                }
            }
        }
        MakeRequest("POST", "https://api.notion.com/v1/pages",
                    "Round Up Transaction", data)
        self.Account.GetRoundUp().ApplyTransaction(self.Amount -
                                                   abs(self.RealAmount))

    def __MakeTunnelTransaction(self):
        data = {
            'parent': {
                'type': 'database_id',
                'database_id': self.__mm.GetTransactionsDBID()
            },
            'properties': {
                'Account': {
                    'type': 'relation',
                    'relation': [{
                        'id': self.Account.GetTunnel()["To"].GetID()
                    }]
                },
                'Amount': {
                    'type': 'number',
                    'number': -self.RealAmount
                },
                'Date': {
                    'type': 'date',
                    "date": {
                        "start": dt.today().isoformat()[:10]
                    }
                },
                'Name': {
                    'type': 'title',
                    'title': [{
                        'type': 'text',
                        'text': {
                            'content': self.Reason
                        }
                    }]
                }
            }
        }
        MakeRequest("POST", "https://api.notion.com/v1/pages",
                    "Tunnel Transaction", data)
        self.Account.GetTunnel()["To"].ApplyTransaction(self.Amount -
                                                        abs(self.RealAmount))

    def GetAccount(self):
        while self.Account == -1:
            print("What account is this transaction on?")
            for index, account in enumerate(self.__mm.GetAccount()):
                print(str(index + 1) + ") " + account.GetName())
            self.Account = input()
            try:
                self.Account = int(self.Account)
                if self.Account not in list(
                        range(1,
                              len(self.__mm.GetAccount()) + 1)):
                    self.Account = -1
                    print("Pick a valid choice")
            except ValueError:
                self.Account = -1
                print("Pick a valid choice")
        self.Account = self.__mm.GetAccount(self.Account - 1)

    def GetExpenseType(self):
        while self.ExpenseType == -1:
            print("What type of transaction is it?")
            for index, type in enumerate(TYPE):
                print(str(index + 1) + ") " + type)
            self.ExpenseType = input()
            try:
                self.ExpenseType = int(self.ExpenseType)
                if self.ExpenseType not in list(range(1, len(TYPE) + 1)):
                    self.ExpenseType = -1
                    print("Pick a valid choice")
            except ValueError:
                self.ExpenseType = -1
                print("Pick a valid choice")
        self.ExpenseType = TYPE[self.ExpenseType - 1]

    def GetAmount(self):
        while self.RealAmount < 0:
            print("How much was this transaction?")
            self.RealAmount = input()
            try:
                self.RealAmount = float(self.RealAmount)
                if self.RealAmount < 0:
                    print("Transaction must be more than 0")
            except ValueError:
                self.RealAmount = -1
                print("Pick a valid choice")
        if self.ExpenseType == "Expense":
            self.RealAmount = -self.RealAmount
        print()

    def GetReason(self):
        print("Sumarise this transaction")
        self.Reason = input()
        print()


MoneyMove(getenv("testlandingurl"))