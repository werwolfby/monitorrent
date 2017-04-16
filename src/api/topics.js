import { throwOnError } from './helper'

const topicParse = /\/api\/topics\/(\d+)\/?/

export default {
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
