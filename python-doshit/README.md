# doshit in python

## example of running doshit

Note you must start the redis-server and `pip install psutil redis`.

### start worker
``` bash
cd python-doshit/examples/
python ../doshit/worker.py tasks
```
The worker waits for a job from redis then excutes the job then stores and broadcast the result in redis.

### calling task and function in python
``` python
from tasks import add
add_result = add.delay(1, 2)
print add_result.wait()
```

## installing doshit

``` bash
cd python-doshit/
python setup.py install
```
or via vituralenvwapper

``` bash
cd python-doshit/
mkvirtualenv doshit --system-site-package
add2virtualenv .
```

