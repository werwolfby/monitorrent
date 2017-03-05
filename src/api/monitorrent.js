function throwOnError (response) {
    if (response.status >= 500 || response.status === 400) {
        return response.json().then(result => {
            const error = new Error(result.title)
            error.status = response.status
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
    },

    deleteTopic (id) {
        return fetch(`/api/topics/${id}`, { method: 'DELETE', body: '' })
            .then(throwOnError)
    },

    defaultClient () {
        return fetch('/api/default_client')
            .then(throwOnError)
            .then(response => response.json())
    },

    parseUrl (url) {
        return fetch('/api/topics/parse?url=' + encodeURIComponent(url))
            .then(throwOnError)
            .then(response => response.json())
    },

    addTopic (url, settings) {
        return fetch('/api/topics', { method: 'POST', body: JSON.stringify({url, settings}) })
            .then(throwOnError)
            .then(response => response.headers.get('Location'))
    }
}
