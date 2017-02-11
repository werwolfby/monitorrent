import api from '../../api/monitorrent'

const SET_TOPICS = 'set_topics'
const LOAD_FAILED = 'load_failed'
const SET_FILTER_STRING = 'set_filter_string'
const SET_ORDER = 'set_order_string'

export const types = {
  SET_FILTER_STRING,
  SET_ORDER
}

const state = {
  topics: [],
  filterString: '',
  order: '-last_update'
}

function smartFilter (topics, filterString) {
  function filterValue (value, filterString) {
    return value.display_name.toLowerCase().indexOf(filterString) > -1 ||
           value.tracker.toLowerCase().indexOf(filterString) > -1
  }

  let filterStringParams = filterString.split(' ').filter(e => e).map(e => e.toLowerCase())
  return topics.filter(t => filterStringParams.every(p => filterValue(t, p)))
}

function smartOrder (topics, order) {
  function getKey (topic, order) {
    let orderValue = topic[order]
    if (order === 'last_update') {
      orderValue = new Date(orderValue || 32503680000000)
    }

    return orderValue
  }

  let reverse = false
  if (order.substring(0, 1) === '-') {
    order = order.substring(1)
    reverse = true
  }

  return [...topics].sort((a, b) => (getKey(a, order) - getKey(b, order)) * (reverse ? -1 : 1))
}

const getters = {
  filteredTopics: state => smartOrder(smartFilter(state.topics, state.filterString), state.order)
}

const actions = {
  async loadTopics ({commit}) {
    try {
      commit(SET_TOPICS, { topics: await api.getTopics() })
    } catch (err) {
      commit(LOAD_FAILED, { err })
    }
  }
}

const mutations = {
  [SET_TOPICS] (state, { topics }) {
    state.topics = topics
  },

  [LOAD_FAILED] (state) {
    // TODO:
  },

  [SET_FILTER_STRING] (state, { value }) {
    state.filterString = value
  },

  [SET_ORDER] (state, { order }) {
    state.order = order
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
