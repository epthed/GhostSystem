Backend/API for [ghostsystem](https://ghostsystem-web.herokuapp.com/).

Install with miniconda: 
```
conda env create -f environment.yml
```
Install PostgreSQL that this process can access

Set environment variables, names below are required, fill in values as needed. 
This assumes running [ghostsystem-web](https://github.com/epthed/GhostSystem-web) locally as well:
```
PORT=5000;  
ORIGINS=http://localhost:8080; 
DATABASE_URL=postgres://postgres@localhost:5432  
```

After creating above environment variables:
```
conda run --no-capture-output -n ghostsystem python main.py
```