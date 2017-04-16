import { throwOnError } from './helper'

const proxyKeyUrl = key => `/api/settings/proxy?key=` + encodeURIComponent(key)

export default {
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
