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

function createPlay (loading, settings) {
    return {
        store: createStore(loading, settings),
        render: (h) => <md-whiteframe md-elevation="5" style="margin: auto; width: 1168px"><SettingsGeneral/></md-whiteframe>
    }
}

play(SettingsGeneral)
    .add('loading', createPlay(true, null))
    .add('partial settings', createPlay(false, partialSettings))
    .add('full settings', createPlay(false, fullSettings))
