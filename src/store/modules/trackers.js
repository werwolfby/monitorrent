import api from '../../api/monitorrent'
import types from '../types'

const state = {
    loading: true,
    error: null,
    trackers: []
}

const getters = {
}

const actions = {
    async loadTrackers ({ commit }) {
        try {
            const trackers = await api.trackers.all()
            commit(types.SET_TRACKERS, trackers)
        } catch (err) {
            commit(types.LOAD_TRACKERS_FAILED, err)
        }
    },

    async loadTracker ({ commit, dispatch, state }, tracker) {
        try {
            if (!state.trackers || state.trackers.length === 0) {
                await dispatch('loadTrackers')
            }
            const model = await api.trackers.tracker(tracker)

            commit(types.SET_TRACKER_MODEL, { tracker, model: model.settings })
        } catch (err) {
        }
    }
}

const mutations = {
    [types.SET_TRACKERS] (state, trackers) {
        state.loading = false
        state.error = null
        state.trackers = trackers
    },

    [types.LOAD_TRACKERS_FAILED] (state, error) {
        state.loading = false
        state.error = error
        state.trackers = []
    },

    [types.SET_TRACKER_MODEL] (state, { tracker, model }) {
        const trackerIndex = state.trackers.findIndex(e => e.name === tracker)
        if (trackerIndex >= 0) {
            state.trackers[trackerIndex] = {...state.trackers[trackerIndex], model}
        }
    }
}

export default {
    state,
    getters,
    actions,
    mutations
}
