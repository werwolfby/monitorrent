import { throwOnError } from './helper'

export default {
    all () {
        return fetch(`/api/trackers`)
            .then(throwOnError)
            .then(response => response.json())
    },

    tracker (tracker) {
        return fetch(`/api/trackers/${tracker}`)
            .then(throwOnError)
            .then(response => response.json())
    },

    save (tracker, settings) {
        return fetch(`/api/trackers/${tracker}`, { method: 'PUT', body: JSON.stringify(settings) })
            .then(throwOnError)
    },

    async check (tracker) {
        const result = await fetch(`/api/trackers/${tracker}/check`)
            .then(throwOnError)
            .then(response => response.json())

        return result.status
    }
}
