export default {
  getTopics () {
    return fetch('/api/topics')
      .then(data => data.json())
  }
}
