import api from '../../api/monitorrent'
import types from '../types'
import { smartFilter, smartOrder } from './filters'

const state = {
    loading: true,
    last_execute: null,
    executing: false,
    topics: [],
    filterString: '',
    order: '-last_update'
}

const getters = {
    filteredTopics: state => smartOrder(smartFilter(state.topics, state.filterString), state.order),
    trackers: state => state.topics.map(t => t.tracker).filter((v, i, a) => a.indexOf(v) === i)
}

const actions = {
    async loadTopics ({commit}) {
        try {
            let topicsPromise = api.getTopics()
            let latestLogsPromise = api.getLogs(0, 1)
            let [topics, log] = await Promise.all([topicsPromise, latestLogsPromise])
            commit(types.SET_TOPICS, { topics })
            commit(types.SET_LAST_EXECUTE, { execute: log.data.length > 0 ? log.data[0] : null })
            commit(types.COMPLETE_LOADING)
        } catch (err) {
            commit(types.LOAD_FAILED, { err })
        }
    },
    async setTopicPaused ({commit, state}, {id, value}) {
        let topic, originalPaused
        try {
            topic = state.topics.filter(t => t.id === id)[0]
            if (!topic) {
                throw new Error(`Can't find topic with ${id} id`)
            }
            originalPaused = topic.paused
            commit(types.SET_TOPIC_PAUSED, {topic, value})
            await api.setTopicPaused(id, value)
        } catch (err) {
            if (topic) {
                commit(types.SET_TOPIC_PAUSED, {topic, value: originalPaused})
            }
        }
    }
}

const mutations = {
    [types.SET_TOPICS] (state, { topics }) {
        state.topics = topics
    },

    [types.SET_LAST_EXECUTE] (state, { execute }) {
        state.last_execute = execute
    },

    [types.LOAD_FAILED] (state, { err }) {
        // TODO:
    },

    [types.SET_FILTER_STRING] (state, { value }) {
        state.filterString = value
    },

    [types.SET_ORDER] (state, { order }) {
        state.order = order
    },

    [types.COMPLETE_LOADING] (state) {
        state.loading = false
    },

    [types.SET_TOPIC_PAUSED] (state, { topic, value }) {
        topic.paused = value
    }
}

export default {
    state,
    getters,
    actions,
    mutations
}
