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
    },
    {
        name: 'tracker4.com',
        form: [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'keypass',
                    label: 'Keypass',
                    flex: 100
                }]
            }
        ]
    },
    {
        name: 'tracker5.com',
        form: [
            {
                type: 'row',
                content: [
                    {
                        type: 'text',
                        model: 'username',
                        label: 'Username',
                        flex: 45
                    },
                    {
                        type: 'password',
                        model: 'password',
                        label: 'Password',
                        flex: 45
                    },
                    {
                        type: 'select',
                        model: 'default_quality',
                        label: 'Default Quality',
                        options: [
                            'SD',
                            '720p',
                            '1080p'
                        ],
                        flex: 10
                    }
                ]
            }
        ]

    }
]

const models = {
    'tracker1.com': null,
    'tracker2.com': null,
    'tracker3.com': {
        username: 'username'
    },
    'tracker4.com': {
        keypass: 'asdqwdasd123asdq123asd12'
    },
    'tracker5.com': {
        username: 'username',
        password: 'password',
        default_quality: '720p'
    }
}

const canCheckes = {
    'tracker4.com': false
}

const log = (msg) => log.log(msg)
log.log = () => {}

function createTrackers ({ loading, trackers, models, canCheckes }) {
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
                const canCheck = !canCheckes || !canCheckes.hasOwnProperty(tracker)
                commit('SET_TRACKER_MODEL', { tracker, model: models[tracker], canCheck })
            }
        },
        mutations: {
            'SET_TRACKERS' (state, trackers) {
                state.loading = false
                state.trackers = trackers
            },
            'SET_TRACKER_MODEL' (state, { tracker, model, canCheck }) {
                const trackerIndex = state.trackers.findIndex(e => e.name === tracker)
                if (trackerIndex >= 0) {
                    state.trackers = [
                        ...state.trackers.slice(0, trackerIndex),
                        {...state.trackers[trackerIndex], model, canCheck},
                        ...state.trackers.slice(trackerIndex + 1)
                    ]
                }
            }
        }
    }
}

function createStoreOptions (params) {
    return {
        modules: {
            trackers: createTrackers(params)
        }
    }
}

const createStore = (params) => new Vuex.Store(createStoreOptions(params))

function createPlay ({tracker, ...params}) {
    return {
        store: createStore(params),
        render: function (h) {
            log.log = this.$log
            return <md-whiteframe md-elevation="5" style="margin: auto; width: 1168px"><SettingsTracker tracker={tracker}/></md-whiteframe>
        }
    }
}

play(SettingsTracker)
    .add('loading', createPlay({loading: true, trackers: [], model: {}, tracker: 'tracker1.com'}))
    .add('tracker without settings', createPlay({loading: false, trackers, models, canCheckes, tracker: 'tracker1.com'}))
    .add('tracker without empty settings', createPlay({loading: false, trackers, models, canCheckes, tracker: 'tracker2.com'}))
    .add('tracker with settings', createPlay({loading: false, trackers, models, canCheckes, tracker: 'tracker3.com'}))
    .add('tracker without check', createPlay({loading: false, trackers, models, canCheckes, tracker: 'tracker4.com'}))
    .add('tracker quality select', createPlay({loading: false, trackers, models, canCheckes, tracker: 'tracker5.com'}))
