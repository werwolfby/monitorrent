import { throwOnError } from './helper'

export default {
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
