function throwOnError (response) {
    if (response.status >= 500 || (response.status === 400 || response.status === 404)) {
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

const topicParse = /\/api\/topics\/(\d+)\/?/

const ExecuteApi = {
    logs (skip = 0, take = 10) {
        return fetch(`/api/execute/logs?skip=${skip}&take=${take}`)
            .then(throwOnError)
            .then(response => response.json())
    },

    current () {
        return fetch(`/api/execute/logs/current`)
            .then(throwOnError)
            .then(response => response.json())
    },

    details (executeId, lastLogId = null) {
        let url = `/api/execute/logs/${executeId}/details`
        if (lastLogId) {
            url = url + `?after=${lastLogId}`
        }
        return fetch(url)
            .then(throwOnError)
            .then(response => response.json())
    },

    execute (ids = null) {
        let url = `/api/execute/call`
        if (ids && ids.length > 0) {
            url = `${url}?ids=${ids.join(',')}`
        }

        return fetch(url, { method: 'POST' })
            .then(throwOnError)
            .then(response => true)
    },

    executeTracker (tracker) {
        return fetch(`/api/execute/call?tracker=${tracker}`, { method: 'POST' })
            .then(throwOnError)
            .then(response => true)
    }
}

const TopicsApi = {
    all () {
        return fetch('/api/topics')
            .then(throwOnError)
            .then(data => data.json())
    },

    get (id) {
        return fetch(`/api/topics/${id}`)
            .then(throwOnError)
            .then(response => response.json())
    },

    setPaused (id, value) {
        return fetch(`/api/topics/${id}/pause`, { method: 'POST', body: JSON.stringify({ paused: value }) })
            .then(throwOnError)
    },

    resetStatus (id) {
        return fetch(`/api/topics/${id}/reset_status`, { method: 'POST', body: '' })
            .then(throwOnError)
    },

    delete (id) {
        return fetch(`/api/topics/${id}`, { method: 'DELETE', body: '' })
            .then(throwOnError)
    },

    parseUrl (url) {
        return fetch('/api/topics/parse?url=' + encodeURIComponent(url))
            .then(throwOnError)
            .then(response => response.json())
    },

    add (url, settings) {
        return fetch('/api/topics', { method: 'POST', body: JSON.stringify({url, settings}) })
            .then(throwOnError)
            .then(response => {
                const location = response.headers.get('Location')
                const match = topicParse.exec(location)

                return parseInt(match[1])
            })
    },

    edit (id, settings) {
        return fetch(`/api/topics/${id}`, { method: 'PUT', body: JSON.stringify(settings) })
            .then(throwOnError)
    }
}

const proxyKeyUrl = key => `/api/settings/proxy?key=` + encodeURIComponent(key)

const SettingsApi = {
    getUpdateInterval () {
        return fetch(`/api/settings/execute`)
            .then(throwOnError)
            .then(response => response.json())
            .then(result => result.interval / 60)
    },
    setUpdateInterval (value) {
        return fetch(`/api/settings/execute`, { method: 'PUT', body: JSON.stringify({interval: value * 60}) })
            .then(throwOnError)
    },
    proxy: {
        isEnabled () {
            return fetch(`/api/settings/proxy/enabled`)
                .then(throwOnError)
                .then(response => response.json())
                .then(result => result.enabled)
        },
        setEnabled (value) {
            return fetch(`/api/settings/proxy/enabled`, { method: 'PUT', body: JSON.stringify({enabled: value}) })
                .then(throwOnError)
        },
        async getUrl (key) {
            const response = await fetch(proxyKeyUrl(key))
            if (response.status === 404) {
                return null
            }
            const json = await response.json()
            return json.url
        },
        setUrl (key, value) {
            if (!value) {
                return fetch(proxyKeyUrl(key), { method: 'DELETE' })
                    .then(throwOnError)
            } else {
                return fetch(proxyKeyUrl(key), { method: 'PUT', body: JSON.stringify({url: value}) })
                    .then(throwOnError)
            }
        }
    },
    getNewVersionChecker () {
        return fetch(`/api/settings/new-version-checker`)
            .then(throwOnError)
            .then(response => response.json())
            .then(result => ({...result, interval: result.interval / 60}))
    },
    updateNewVersionChecker (value) {
        if ('interval' in value) {
            value = {...value, interval: value.interval * 60}
        }
        return fetch(`/api/settings/new-version-checker`, { method: 'PATCH', body: JSON.stringify(value) })
            .then(throwOnError)
    }
}

export default {
    defaultClient () {
        return fetch('/api/default_client')
            .then(throwOnError)
            .then(response => response.json())
    },

    topics: TopicsApi,
    execute: ExecuteApi,
    settings: SettingsApi
}
