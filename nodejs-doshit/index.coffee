redis = require 'redis'
uuid = require 'uuid'
moment = require 'moment'
EventEmitter = require('events').EventEmitter
util = require 'util'

startswith = (s, prefix, position) ->
  position ?= 0
  s.indexOf(prefix, position) is position

Doshit = (url, appprefix, queueprefix) ->
  EventEmitter.call @

  doshit = @

  resultschannel = "#{appprefix}:results"
  pendinglist = "#{appprefix}:#{queueprefix}:pending"
  taskprefix = "#{appprefix}:task:"

  taskcallbacks = {}

  queries = redis.createClient url: url
  subscriptions = redis.createClient url: url

  subscriptions.on 'message', (channel, message) ->
    return unless channel is resultschannel
    return unless startswith message, ''
    taskid = message.substr taskprefix.length
    return if !taskcallbacks[taskid]?
    doshit.gettask taskid, (err, task) ->
      if err?
        doshit.emit 'error', err
        return
      return if task.state isnt 'finished'
      if task.result is 'successful'
        for cb in taskcallbacks[taskid]
          cb null, task['result-value'], task
          doshit.emit 'success', task['result-value'], task
      else if task.result is 'failed'
        for cb in taskcallbacks[taskid]
          cb task['error-exception'] ? task, null, task
          doshit.emit 'failure', task['error-exception'], task

  subscriptions.subscribe resultschannel

  @task = (name, args, cb) =>
    taskid = uuid.v4()
    taskcallbacks[taskid] = [] if !taskcallbacks[taskid]?
    taskcallbacks[taskid].push cb
    task =
      function: name
      state: 'pending'
      args: JSON.stringify args, null, 2
    queries.hmset "#{taskprefix}#{taskid}", task, (err) ->
      if err?
        cb err
        doshit.emit 'error', err
        return
      queries.lpush pendinglist, taskid, (err) ->
        if err?
          cb err
          doshit.emit 'error', err
          return
    taskid

  @gettask = (taskid, cb) ->
    queries.hgetall "#{taskprefix}#{taskid}", (err, task) ->
      return cb err if err?
      for f in ['args', 'result-value']
        continue if !task[f]?
        task[f] = JSON.parse task[f]
      for f in ['executing-created', 'finished-created']
        continue if !task[f]?
        task[f] = moment.utc(task[f], 'YYYY-MM-DD[T]HH:mm:ss.SSSSSS[Z]').toDate()
      cb null, task

  @quit = ->
    queries.quit()
    subscriptions.quit()

  @end = ->
    queries.end()
    subscriptions.end()

  @

util.inherits Doshit, EventEmitter
module.exports = (url, appprefix, queueprefix) -> new Doshit url, appprefix, queueprefix