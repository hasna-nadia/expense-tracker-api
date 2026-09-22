from fastapi import FastAPI
import transactions
import models
import auth
from database import engine


app = FastAPI()


models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(transactions.router)


@app.get("/")
def home():
    return {"message": "Expense Tracker API is running"}