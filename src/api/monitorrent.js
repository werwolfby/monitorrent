export default {
    getTopics () {
        return fetch('/api/topics')
              .then(data => data.json())
    },

    getLogs (skip = 0, take = 10) {
        return fetch(`/api/execute/logs?skip=${skip}&take=${take}`)
              .then(response => response.json())
    },

    setTopicPaused (id, value) {
        return fetch(`/api/topics/${id}/pause`, { method: 'POST', body: JSON.stringify({ paused: value }) })
            .then(resp => {
                if (resp.status >= 500) {
                    return resp.json().then(result => {
                        let error = new Error(result.title)
                        error.description = result.description
                        throw error
                    })
                }

                return resp
            })
    }
}
