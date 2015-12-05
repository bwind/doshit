# dothis in python

## install doshit

``` bash
cd python-dothis/
python setup.py install
```
or via vituralenvwapper

``` bash
cd python-dothis/
mkvirtualenv doshit --system-site-package
add2virtualenv .
```

## exmample of how to run.

### start redis-server
``` bash
redis-server
```

### start worker
``` bash
cd python-dothis/examples/
python ../dothis/worker.py tasks
```

### call task / method in python
``` bash
python
```
``` python
from tasks import add
add_result = add.delay(1, 2)
print add_result.wait()
```
