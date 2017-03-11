import api from '../../api/monitorrent'
import types from '../types'

const state = {
    loading: true,
    last_execute: null,
    executing: false
}

const getters = {
}

const actions = {
    async loadLastExecute ({commit}) {
        try {
            let logs = await api.execute.logs(0, 1)
            commit(types.SET_LAST_EXECUTE, { execute: logs.data.length > 0 ? logs.data[0] : null })
        } catch (err) {
            commit(types.LOAD_EXECUTE_FAILED, { err })
        }
    }
}

const mutations = {
    [types.SET_LAST_EXECUTE] (state, { execute }) {
        state.loading = false
        state.last_execute = execute
    },

    [types.LOAD_EXECUTE_FAILED] (state, { err }) {
        state.loading = false
        state.last_execute = null
    }
}

export default {
    state,
    getters,
    actions,
    mutations
}
