# dothis
Job queue for Python and NodeJS using Redis.



## how to use dothis in REDIS directly.

### Creating a task

Creating a task is done in two steps:

1) create a hash describing the task attributes in redis:

``` bash
HSET {queue_name}:task:{task_id} function {function_name}
HSET {queue_name}:task:{task_id} state pending
HSET {queue_name}:task:{task_id} function {args}
```

note: args is a json string '{"name": "gregc", "age": 35}' and you must state each parameter name, arrays or args is not accepted

2) push the task to the pending list / queue:

``` bash
LPUSH {queue_name}:task:{task_id} {queue_name}:task:{task_id}
```
example:
``` bash
HSET dothis:task:11111111-2222-2222-2222-333333333333 function echo
HSET dothis:task:11111111-2222-2222-2222-333333333333 state pending
HSET dothis:task:11111111-2222-2222-2222-333333333333 args '{ "text": "ooh yeeah" }'
LPUSH dothis:pending 11111111-2222-2222-2222-333333333333

to get the result:

HMGET dothis:task:11111111-2222-2222-2222-333333333333 result result-value
1) "successful"
2) "\"ooh yeeah\""
```

Your done!

### waiting for a job's results

to see when a job is finished you can poll or better yet subcribe to the results PUBSUB channel.

#### polling result

``` bash
HMGET {queue_name}:task:{task_id} result result-value
```
if no result has been posted you will get: 1) (nil) 2) (nil)

example:
``` bash
127.0.0.1:6379> HMGET dothis:task:47b87457-fbdb-4f2e-8222-2a322bfb4f61 result result-value
1) "successful"
2) "\"ooh yeeah\""
```

#### PUBSUB SUBSCRIBE for result.

``` bash
SUBSCRIBE {queue_name}:results
```
subscribe to the queues channel.

``` bash
HMGET {queue_name}:task:{task_id} result result-value
```
then go get the result's details if your interested.

example:
``` bash
127.0.0.1:6379> SUBSCRIBE dothis:results
Reading messages... (press Ctrl-C to quit)
1) "subscribe"
2) "dothis:results"
3) (integer) 1
1) "message"
2) "dothis:results"
3) "dothis:task:518696a2-6c41-4456-8d6e-76ac29ad77dd"
1) "message"
2) "dothis:results"
3) "dothis:task:47b87457-fbdb-4f2e-8222-2a322bfb4f61"
1) "message"
2) "dothis:results"
3) "dothis:task:8e0d0bbc-e0d7-44f6-813d-92807603f016"
```

### more schema print outs from REDIS.

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
