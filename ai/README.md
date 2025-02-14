# AI Backend


## Installation on GCE

- install ffmpeg
```bash
sudo snap install ffmpeg
```

- install miniconda
```bash
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
```

- create conda environment
```bash
conda create -n tsmc python=3.11
conda activate tsmc
```

- install dependencies
```bash
pip install -r requirements.txt
```