export default {
  getTopics () {
    let p = new Promise(resolve => {
      setTimeout(() => {
        resolve([])
      }, 2000)
    })

    return p.then(() => fetch('/api/topics')
        .then(data => data.json()))
  }
}
