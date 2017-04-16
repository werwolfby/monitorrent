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
    }
}
