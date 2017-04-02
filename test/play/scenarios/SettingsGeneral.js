import Vuex from 'vuex'
import { play } from 'vue-play'
import SettingsGeneral from '../../../src/components/Settings/SettingsGeneral'

function wrap (h, el) {
    return <md-whiteframe md-elevation="5" style="margin: auto; width: 1168px">{el}</md-whiteframe>
}

const defaultSettings = {
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

function createSettings (loading, settings) {
    return {
        state: {
            loading: true,
            settings: null
        },
        actions: {
            loadSettings ({ commit }) {
                commit('SET_SETTINGS', settings)
                commit('SET_SETTINGS_LOADING', { value: loading })
            }
        },
        mutations: {
            'SET_SETTINGS_LOADING' (state, { value }) {
                state.loading = value
            },
            'SET_SETTINGS' (state, settings) {
                state.settings = settings
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

play(SettingsGeneral)
    .add('loading', {
        store: createStore(true, null),
        render: (h) => wrap(h, <SettingsGeneral/>)
    })
    .add('full settings', {
        store: createStore(false, defaultSettings),
        render: (h) => wrap(h, <SettingsGeneral/>)
    })
