
from threading import Thread
from eurusd_bot import run_eurusd
from gold_bot import run_gold

t1 = Thread(target=run_eurusd)
t2 = Thread(target=run_gold)

t1.start()
t2.start()
