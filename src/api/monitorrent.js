export default {
  getTopics () {
    let p = new Promise(resolve => {
      setTimeout(() => {
        resolve([])
      }, 2000)
    })

    return p.then(() => fetch('/api/topics')
        .then(data => data.json()))
  },

  getLogs (skip = 0, take = 10) {
    return fetch(`/api/execute/logs?skip=${skip}&take=${take}`)
      .then(response => response.json())
  }
}
