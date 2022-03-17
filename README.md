# Reddit Productivity Info 159 Project
## Annotating
Running annotation will produce an `annotations.csv` file.
```bash
./annotate.sh
```

## Getting data
Make sure you have [Reddit API credentials](https://praw.readthedocs.io/en/stable/getting_started/quick_start.html#read-only-reddit-instances) saved in a file called `credentials.json` in this folder.

```bash
pip install -r requirements.txt
python get_data.py
```
