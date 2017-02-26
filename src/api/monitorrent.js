function throwOnError (response) {
    if (response.status >= 500) {
        return response.json().then(result => {
            let error = new Error(result.title)
            error.description = result.description
            throw error
        })
    } else if (response.status >= 300) {
        return response.text().then(result => {
            throw new Error(result)
        })
    }

    return response
}

export default {
    getTopics () {
        return fetch('/api/topics')
            .then(throwOnError)
            .then(data => data.json())
    },

    getLogs (skip = 0, take = 10) {
        return fetch(`/api/execute/logs?skip=${skip}&take=${take}`)
            .then(throwOnError)
            .then(response => response.json())
    },

    setTopicPaused (id, value) {
        return fetch(`/api/topics/${id}/pause`, { method: 'POST', body: JSON.stringify({ paused: value }) })
            .then(throwOnError)
    },

    resetTopicStatus (id) {
        return fetch(`/api/topics/${id}/reset_status`, { method: 'POST', body: '' })
            .then(throwOnError)
    }
}
