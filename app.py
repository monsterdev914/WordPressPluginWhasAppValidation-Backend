from fastapi import FastAPI, status
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel
import json
import httpx
import os
import time
import uvicorn
app = FastAPI()
scheduler = AsyncIOScheduler()


class Account(BaseModel):
    API_KEY: str
    NUMBER_ID: str


def sync_device(account):
    try:
        response = httpx.get(f"https://api.wassenger.com/v1/devices/{account['NUMBER_ID']}/sync", headers={"Token": account['API_KEY']})
        print(f"Synced device {account['NUMBER_ID']}: {response.text}")
    except Exception as e:
        print(f"Error syncing device {account['NUMBER_ID']}: {e}")


def timed_task():
    # if file is not found, create it
    if not os.path.exists("wassenger_accounts.json"):
        with open("wassenger_accounts.json", "w") as f:
            json.dump([], f, indent=4)
    with open("wassenger_accounts.json", "r") as f:
        accounts = json.load(f)
    for account in accounts:
        sync_device(account)


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(timed_task, "interval", minutes=2)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

    
@app.get("remove_account/{number_id}", status_code=status.HTTP_200_OK)
def remove_account(number_id: str):
    try:
        with open("wassenger_accounts.json", "r") as f:
            accounts = json.load(f)
        for account in accounts:
            if account['NUMBER_ID'] == number_id:
                accounts.remove(account)
                break
        with open("wassenger_accounts.json", "w") as f:
            json.dump(accounts, f, indent=4)
        return {"message": "Account removed successfully"}
    except Exception as e:
        return {"message": f"Error removing account: {e}"}, status.HTTP_500_INTERNAL_SERVER_ERROR


@app.post("/add_account", status_code=status.HTTP_201_CREATED)
def add_account(new_account: Account):
    try:
        # Read existing accounts
        try:
            with open("wassenger_accounts.json", "r") as f:
                accounts = json.load(f)
        except FileNotFoundError:
            accounts = []
        
        # Check if account already exists
        for account in accounts:
            if account['NUMBER_ID'] == new_account.NUMBER_ID:
                return {"message": "Account already exists"}, status.HTTP_400_BAD_REQUEST
        
        # Add new account
        accounts.append(new_account.dict())
        
        # Write back to file
        with open("wassenger_accounts.json", "w") as f:
            json.dump(accounts, f, indent=4)
        
        return {"message": "Account added successfully"}
    except Exception as e:
        return {"message": f"Error adding account: {e}"}, status.HTTP_500_INTERNAL_SERVER_ERROR


@app.get("/")
def read_root():
    return {"message": "Hello World"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
