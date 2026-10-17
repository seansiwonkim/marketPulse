from fastapi import FastAPI

app = FastAPI(title="marketPulse")


@app.get("/health")
def health():
    return {"status": "ok"}
