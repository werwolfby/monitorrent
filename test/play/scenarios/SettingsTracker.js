import Vuex from 'vuex'
import { play } from 'vue-play'
import SettingsTracker from '../../../src/components/Settings/SettingsTracker'

const trackers = [
    {name: 'tracker1.com', form: null},
    {
        name: 'tracker2.com',
        form: [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 50
                }, {
                    type: 'password',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]
    },
    {
        name: 'tracker3.com',
        form: [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 50
                }, {
                    type: 'password',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]
    }
]

const models = {
    'tracker1.com': null,
    'tracker2.com': null,
    'tracker3.com': {
        username: 'username'
    }
}

const log = (msg) => log.log(msg)
log.log = () => {}

function createTrackers (loading, trackers, models) {
    return {
        state: {
            loading: true,
            trackers: []
        },
        actions: {
            loadTrackers ({ commit }) {
                log('loadSettings')
                if (!loading) {
                    commit('SET_TRACKERS', trackers)
                }
            },
            loadTracker ({ commit, state }, tracker) {
                log(`loadTracker ${tracker}`)
                if (!loading && (!state.trackers || state.trackers.length === 0)) {
                    commit('SET_TRACKERS', trackers)
                }
                commit('SET_TRACKER_MODEL', { tracker, model: models[tracker] })
            }
        },
        mutations: {
            'SET_TRACKERS' (state, trackers) {
                state.loading = false
                state.trackers = trackers
            },
            'SET_TRACKER_MODEL' (state, { tracker, model }) {
                const trackerIndex = state.trackers.findIndex(e => e.name === tracker)
                if (trackerIndex >= 0) {
                    state.trackers = [
                        ...state.trackers.slice(0, trackerIndex),
                        {...state.trackers[trackerIndex], model},
                        ...state.trackers.slice(trackerIndex + 1)
                    ]
                }
            }
        }
    }
}

function createStoreOptions (loading, trackers, models) {
    return {
        modules: {
            trackers: createTrackers(loading, trackers, models)
        }
    }
}

const createStore = (loading, trackers, models) => new Vuex.Store(createStoreOptions(loading, trackers, models))

function createPlay (loading, trackers, models, tracker) {
    return {
        store: createStore(loading, trackers, models),
        render: function (h) {
            log.log = this.$log
            return <md-whiteframe md-elevation="5" style="margin: auto; width: 1168px"><SettingsTracker tracker={tracker}/></md-whiteframe>
        }
    }
}

play(SettingsTracker)
    .add('loading', createPlay(true, [], {}, 'tracker1.com'))
    .add('tracker without settings', createPlay(false, trackers, models, 'tracker1.com'))
    .add('tracker without empty settings', createPlay(false, trackers, models, 'tracker2.com'))
    .add('tracker with settings', createPlay(false, trackers, models, 'tracker3.com'))
