## Create/Start virtual environment

### For windows user (Powershell)

1. Create virtual environment

```
python -m venv env
```

2. Start virtual environment

```
.\env\Scripts\activate
```

3. Install python packages

```
pip install -r requirements.txt
```

### For MacOS/Linux user

1. Create virtual environment

```
python3 -m venv env
```

2. Start virtual environment

```
source env/bin/activate
```

3. Install python packages

```
pip install -r requirements.txt
```

## Startup database by Docker

1.  Pull MySQL image

```
docker pull mysql:8.1
```

2. Run container

```
docker run --name tsmc_2025_careerhack -e MYSQL_USER=admin -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=tsmc_2025_careerhack -p 3306:3306 --volume tsmc_2025_careerhack:/var/lib/mysql -d mysql:8.1

## Start uvicorn server

```

python main.py

```

## After starting server , to open swagger

```

http://127.0.0.1:8080/docs (open it on browser)

```

```
