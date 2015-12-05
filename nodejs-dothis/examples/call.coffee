doshit = require '../'
client = doshit 'redis://docker:6379', 'dothis'

client.task 'add', { a: 1, b: 5 }, (err, result, task) ->
  return console.error err if err?
  console.log "1 + 5 = #{result}"

client.task 'echo', { text: 'YARR' }, (err, result, task) ->
  return console.error err if err?
  console.log "YARR in, #{result} out"

client.task 'error', {}, (err, result, task) ->
  return console.error err if err?
