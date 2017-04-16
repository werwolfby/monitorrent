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
    }
}

export default {
    state,
    getters,
    actions,
    mutations
}
