Generate puzzles from a game database.

```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python3 generator.py -f file.pgn -t 6 -v -u http://localhost:8000/puzzle
```

prod:

```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.8
sudo apt install -y python3.8-venv
cd
git clone https://github.com/ornicar/lichess-puzzler
cd lichess-puzzler/generator
python3.8 -m venv venv
. venv/bin/activate
python3.8 -m pip install -r requirements.txt
nice -n19 python3.8 generator.py -t 4 -v --url=http://knarr:9371 --token=*** -e /root/fishnet-nv8Icl/stockfish-x86-64-avx512 -f /root/lichess-puzzler/data/lichess_db_standard_rated_2022-08.pgn.zst --parts 2 --part 1 --skip 0
```
