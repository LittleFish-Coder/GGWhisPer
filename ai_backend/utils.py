from google.cloud import storage


"""
Language code reference:
原始: raw (麥克風串流 經過Speech2Text的結果 四國語言穿插)
精準: precise (WAV音檔 經過Speech2Text的結果 四國語言穿插)
中文: zh
英文: en
日文: ja
德文: de 
"""

# download audio from GCS
def download_wav(bucket_name, audio_id="Training"):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    source_blob_name = f"wav/{audio_id}.wav"

    # The path to which the file should be downloaded
    destination_file_name = f"./{audio_id}.wav"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(f"Audio downloaded to {destination_file_name}.")

# download transcript from GCS
def download_transcript(bucket_name, file_id="meeting_transcript", lang="zh"):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    source_blob_name = f"transcript/{lang}/{file_id}.txt"

    # The path to which the file should be downloaded
    destination_file_name = f"./{file_id}.txt"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(f"Transcript downloaded to {destination_file_name}.")

# upload transcript to GCS
def upload_transcript(bucket_name, file_id="sample", lang="zh", transcript_path="../Speech2Text/transcript_cmn-Hant-TW.txt"):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    destination_blob_name = f"transcript/{lang}/{file_id}.txt"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(f"./{transcript_path}")

    print(f"File uploaded to {bucket_name}/{destination_blob_name}.")

# download summary from GCS
def download_summary(bucket_name, file_id="sample", lang="zh"):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    source_blob_name = f"summary/{lang}/{file_id}.md"

    # The path to which the file should be downloaded
    destination_file_name = f"./{file_id}.md"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(f"Summary downloaded to {destination_file_name}.")

# upload summary to GCS
def upload_summary(bucket_name, file_id="sample", lang="zh", content=""):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    destination_blob_name = f"summary/{lang}/{file_id}.md"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(content.encode('utf-8'))

    print(f"File uploaded to {bucket_name}/{destination_blob_name}.")

# upload term to GCS
def upload_term(bucket_name, file_id="sample", lang="zh", file_path="../Speech2Text/terms_cmn-Hant-TW.txt"):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    destination_blob_name = f"term/{lang}/{file_id}.txt"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(f"./{file_path}")

    print(f"File uploaded to {bucket_name}/{destination_blob_name}.")

# upload description to GCS
def upload_description(bucket_name, file_id="sample", lang="zh", file_path="../Speech2Text/description_cmn-Hant-TW.txt"):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    destination_blob_name = f"description/{lang}/{file_id}.txt"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(f"./{file_path}")

    print(f"File uploaded to {bucket_name}/{destination_blob_name}.")

# download description from GCS
def download_description(bucket_name, file_id="sample", lang="zh"):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    source_blob_name = f"description/{lang}/{file_id}.txt"

    # The path to which the file should be downloaded
    destination_file_name = f"./{file_id}.txt"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(f"Description downloaded to {destination_file_name}.")

# upload audio to GCS
def upload_wav(bucket_name, audio_id="sample", audio_path="./src/wav/Training.wav", lang=""):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    bucket_name = "hackathon-c2"

    # The ID of your GCS object
    if not lang:
        destination_blob_name = f"wav/{audio_id}.wav"
    else:
        destination_blob_name = f"wav/{lang}/{audio_id}.mp3"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(f"./{audio_path}")

    print(f"File uploaded to {bucket_name}/{destination_blob_name}.")

if __name__ == "__main__":
    # test    
    # BUCKET_NAME = "hackathon-c2"
    BUCKET_NAME = "hackathon-c2"
    # upload_wav(BUCKET_NAME, audio_id="sample", audio_path="./src/wav/Training.wav")
    # download_wav(BUCKET_NAME, audio_id="50")

    # upload wav
    download_wav(BUCKET_NAME, audio_id="Training")
    # upload_wav(BUCKET_NAME, audio_id="Training", audio_path="../dataset/Training/Training.wav")