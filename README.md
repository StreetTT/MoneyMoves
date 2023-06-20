# MoneyMoves
A notions integrated application to manage money flowing through multiple account and display the information. 

## Set Up

1. Set Up Notion
	
	1. Create a [Notion Account](https://www.notion.so/product)
  	
	2. Create a copy of the [Landing Page](https://valiant-silica-d27.notion.site/MoneyMoves-Template-a2e628aecc714c52802ddd8a572cbcee) in your notion

1. Create Notion integration
  	
	3. Go to the [Integrations](https://www.notion.so/my-integrations) page in your Notion account.
  	
	4. Click the "New integration" button.
  	
	5. Give your integration a name and description.
  	
	6. Select "Private integration" as the integration type.
 	
	7. Click "Create integration".

3. Install Aplication
  	
	1. Clone the repository or download the program as a zip file and unzip it. 
  	
	2. In the root directory of the program, edit `.env` and change the following environment variables: 
  	
	`notiontoken`: Your Internal Integration Token, hiden in the new integration just created  
  
  	![image](https://user-images.githubusercontent.com/33423299/209343663-8be6a295-af39-45db-a4fe-bbbf1a21d404.png)
  
  	`landingurl`: The URL of the coppied page
  
  	![image](https://user-images.githubusercontent.com/33423299/229369429-2cdcb09c-8b21-4878-a365-9d0ed8074cff.png)
   	
	3. Install the required dependencies by running `pip install -r requirements.txt.` in the root directory of the program

## Settings

Name: 
- Name of the Account

Round Ups:
- This rounds up all expenses to the nearest pound and deposits the diffrence into the account linked. 
- The linked account should be entered into the `Round Up To` column
- Leave the `Round Up To` column empty to disable the feature on the account.

Tunnels:
- This connects to accounts together, so that expenses/incomes from one account are payed in to/taken from the linked account.
- To determine if this happens when money is payed in/out of the account, select a drop down option in the `Tunnel When` column
- The linked account the money is payed in/out to should be entered into the `Tunnel To` column
- Leave **either** the `Tunnel When` column or the `Tunnel To` column to disable the feature for the account

