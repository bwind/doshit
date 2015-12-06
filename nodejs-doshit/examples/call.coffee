doshit = require '../'
client = doshit 'redis://docker:6379', 'doshit'

client.on 'success', (result, task) ->
  console.log task

client.task 'add', { a: 1, b: 5 }, (err, result, task) ->
  if err?
    client.quit()
    console.error err
    return

  console.log "1 + 5 = #{result}"

  client.task 'echo', { text: 'YARR' }, (err, result, task) ->
    if err?
      client.quit()
      console.error err
      return

    console.log "YARR in, #{result} out"

    client.task 'error', {}, (err, result, task) ->
      if err?
        client.quit()
        console.error err
        return

      client.quit()
