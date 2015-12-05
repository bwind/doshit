# dothis
Job queue for Python and NodeJS using Redis


``` bash
127.0.0.1:6379> keys * 
1) "dothis:pending"
2) "dothis:worker:f06b9775-22fe-45d6-8f9b-ec9d5d3e1cb5"
3) "dothis:task:963eddf6-e577-48b1-9fec-3c19bbdf2365"
4) "dothis:task:bb3b960c-0067-4d5d-897a-82135f8bcbb4"
5) "dothis:task:762561ae-96a4-4455-852e-8cf86d182136"
6) "dothis:task:963eddf6-e577-48b1-9fec-3c19bbdf2365"
7) "dothis:task:def20874-1c92-4d9b-82b1-c3a3b359da07"
```

``` bash
127.0.0.1:6379> LRANGE dothis:pending 0 -1
1) "762561ae-96a4-4455-852e-8cf86d182136"
2) "963eddf6-e577-48b1-9fec-3c19bbdf2365"
```

``` bash
127.0.0.1:6379> LRANGE dothis:executing 0 -1
1) "def20874-1c92-4d9b-82b1-c3a3b359da07"
```

``` bash
HGETALL dothis:task:bb3b960c-0067-4d5d-897a-82135f8bcbb4 
 1) "function"
 2) "echo"
 3) "state"
 4) "finished"
 5) "args"
 6) "{\n  \"text\": \"it worked!\"\n}"
 7) "pending-created"
 8) "2015-12-05T00:19:01.834909Z"
 9) "executing-created"
10) "2015-12-05T00:19:01.835324Z"
11) "result-value"
12) "\"it worked!\""
13) "result"
14) "successful"
15) "finished-created"
16) "2015-12-05T00:19:01.835429Z"
```
