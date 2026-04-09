# Lab 1 - Hello World

## Create **'reqirements.txt'**
```
pip freeze > requirements.txt
```
or
```
pip install pipreqs
pipreqs .
```

## Step 1: Install libraries
```
pip install fastapi
```
or 
```
pip install -r requirements.txt
```

## Step 2: Run Application
```
unicorn main:api --port 9999
```
or
```
fastapi dev main.py --port 9999
```

## References
- [Youtube: NeuralNine = FastAPI Full Crash Course](https://www.youtube.com/watch?v=rvFsGRvj9jo)