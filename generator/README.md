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
python3.8 -m venv venv
. venv/bin/activate
python3.8 -m pip install -r requirements.txt
nice -n19 python3.8 generator.py -t 4 -v --url=http://godot.lichess.ovh:9371 --token=**** -e /home/fishnet/stockfish-x86_64-bmi2 -f ../data/lichess_db_standard_rated_2020-07.pgn.bz2
```
