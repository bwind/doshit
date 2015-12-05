redis = require 'redis'
uuid = require 'uuid'
moment = require 'moment'

startswith = (s, prefix, position) ->
  position ?= 0
  s.indexOf(prefix, position) is position

module.exports = (url, queue) ->
  resultschannel = "#{queue}:results"
  pendinglist = "#{queue}:pending"
  taskprefix = "#{queue}:task:"

  taskcallbacks = {}

  queries = redis.createClient url: url
  subscriptions = redis.createClient url: url

  subscriptions.on 'message', (channel, message) ->
    return unless channel is resultschannel
    return unless startswith message, ''
    taskid = message.substr taskprefix.length
    return if !taskcallbacks[taskid]?
    queries.hgetall "#{taskprefix}#{taskid}", (err, task) ->
      return if task.state isnt 'finished'
      for f in ['args', 'result-value']
        continue if !task[f]?
        task[f] = JSON.parse task[f]
      for f in ['executing-created', 'finished-created']
        continue if !task[f]?
        task[f] = moment.utc(task[f], 'YYYY-MM-DD[T]HH:mm:ss.SSSSSS[Z]').toDate()
      if task.result is 'successful'
        cb null, task['result-value'], task for cb in taskcallbacks[taskid]
      else if task.result is 'failed'
        cb task['error-exception'] ? task, null, task for cb in taskcallbacks[taskid]

  subscriptions.subscribe resultschannel

  task: (name, args, cb) ->
    taskid = uuid.v4()
    taskcallbacks[taskid] = [] if !taskcallbacks[taskid]?
    taskcallbacks[taskid].push cb
    task =
      function: name
      state: 'pending'
      args: JSON.stringify args, null, 2
    queries.hmset "#{taskprefix}#{taskid}", task, (err) ->
      return cb err if err?
      queries.lpush pendinglist, taskid, (err) ->
        return cb err if err?

  quit: ->
    queries.quit()
    subscriptions.quit()
  end: ->
    queries.end()
    subscriptions.end()