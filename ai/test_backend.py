import requests

def get_summary(file_id="meeting_transcript"):
    #  get
    url = f"http://localhost:8000/summarize/{file_id}"
    response = requests.get(url)
    summary = response.json()
    print(summary)

if __name__ == "__main__":
    get_summary("file")


