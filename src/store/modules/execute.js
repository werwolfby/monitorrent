import api from '../../api/monitorrent'
import types from '../types'

const state = {
    loading: true,
    last_execute: null,
    executing: false,
    current_execute_logs: []
}

const getters = {
}

var watching = false

function unsubscribe () {
    watching = false
}

const actions = {
    async loadLastExecute ({ commit }) {
        try {
            const logs = await api.execute.logs(0, 1)
            commit(types.SET_LAST_EXECUTE, { execute: logs.data.length > 0 ? logs.data[0] : null })
        } catch (err) {
            commit(types.LOAD_EXECUTE_FAILED, { err })
        }
    },

    watchExecuteCurrent ({ dispatch }) {
        watching = true
        return {
            executeCurrentPromise: dispatch('executeCurrent'),
            unsubscribe: unsubscribe
        }
    },

    async executeCurrent ({ dispatch }) {
        let isWatching = watching
        while (isWatching) {
            const result = await api.execute.current()
            if (result.is_running && result.logs && result.logs.length > 0) {
                await dispatch('executeDetails', { id: result.logs[0].execute_id })
            }
            isWatching = watching
        }
    },

    async executeDetails ({ commit, state }, { id }) {
        let result = null
        let currentExecuteLogs = []

        commit(types.SET_EXECUTING, { value: true })
        commit(types.SET_CURRENT_EXECUTE_LOGS, { logs: currentExecuteLogs })

        let logId = null

        do {
            result = await api.execute.details(id, logId)
            if (result.logs && result.logs.length > 0) {
                currentExecuteLogs = [...currentExecuteLogs, ...result.logs]
                commit(types.SET_CURRENT_EXECUTE_LOGS, { logs: currentExecuteLogs })
                logId = result.logs[result.logs.length - 1].id
            }
        } while (result.is_running)

        const logs = await api.execute.logs(0, 1)
        commit(types.SET_LAST_EXECUTE, { execute: logs.data.length > 0 ? logs.data[0] : null })
        commit(types.SET_EXECUTING, { value: false })
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
    },

    [types.SET_EXECUTING] (state, { value }) {
        state.executing = value
    },

    [types.SET_CURRENT_EXECUTE_LOGS] (state, { logs }) {
        state.current_execute_logs = logs
    }
}

export default {
    state,
    getters,
    actions,
    mutations
}
