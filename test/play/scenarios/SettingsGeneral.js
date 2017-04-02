import Vuex from 'vuex'
import { play } from 'vue-play'
import SettingsGeneral from '../../../src/components/Settings/SettingsGeneral'

const fullSettings = {
    updateInterval: 123,
    proxy: {
        enabled: true,
        http: 'http://login:password@proxy.local:8888',
        https: 'https://login:password@proxy.local:8888'
    },
    newVersionCheck: {
        enabled: true,
        preRelease: false,
        interval: 67
    }
}

const partialSettings = {
    updateInterval: 321,
    proxy: {
        enabled: false,
        http: null,
        https: 'https://login:password@proxy.local:8888'
    },
    newVersionCheck: {
        enabled: true,
        preRelease: true,
        interval: 54
    }
}

const log = (msg) => log.log(msg)
log.log = () => {}

function createSettings (loading, settings) {
    return {
        state: {
            loading: true,
            settings: null
        },
        actions: {
            loadSettings ({ commit }) {
                log('loadSettings')
                commit('SET_SETTINGS', settings)
            },
            setProxyEnabled ({ commit }, value) {
                log(`setProxyEnabled = ${value}`)
                commit('SET_PROXY_ENABLED', { value })
            },
            setProxy ({ commit }, params) {
                log(`setProxy ${params.type} = ${params.value}`)
                commit('SET_PROXY', params)
            }
        },
        mutations: {
            'SET_SETTINGS' (state, settings) {
                state.loading = false
                state.settings = settings
            },
            'SET_PROXY_ENABLED' (state, { value }) {
                state.settings.proxy.enabled = value
            },
            'SET_PROXY' (state, { type, value }) {
                state.settings.proxy[type] = value
            }
        }
    }
}

function createStoreOptions (loading, settings) {
    return {
        modules: {
            settings: createSettings(loading, settings)
        }
    }
}

const createStore = (loading, settings) => new Vuex.Store(createStoreOptions(loading, settings))

function createPlay (loading, settings) {
    return {
        store: createStore(loading, settings),
        render: function (h) {
            log.log = this.$log
            return <md-whiteframe md-elevation="5" style="margin: auto; width: 1168px"><SettingsGeneral/></md-whiteframe>
        }
    }
}

play(SettingsGeneral)
    .add('loading', createPlay(true, null))
    .add('partial settings', createPlay(false, partialSettings))
    .add('full settings', createPlay(false, fullSettings))
