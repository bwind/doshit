# dothis in python



## exmample

### start redis-server
``` bash
redis-server
```

### start worker
``` bash
cd python-dothis/examples/
python ../dothis/worker.py tasks
```
The worker waits for a job from redis then excutes the job then stores and broadcast the result in redis.<br/>

### calling task and function in python
``` python
from tasks import add
add_result = add.delay(1, 2)
print add_result.wait()
```

## installing dothis

``` bash
cd python-dothis/
python setup.py install
```
or via vituralenvwapper

``` bash
cd python-dothis/
mkvirtualenv dothis --system-site-package
add2virtualenv .
```

