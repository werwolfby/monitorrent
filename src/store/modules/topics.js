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
  filteredTopics: state => smartOrder(smartFilter(state.topics, state.filterString), state.order)
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
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
