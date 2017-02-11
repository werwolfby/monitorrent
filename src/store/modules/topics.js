import api from '../../api/monitorrent'

const SET_TOPICS = 'set_topics'
const LOAD_FAILED = 'load_failed'
const SET_FILTER_STRING = 'set_filter_string'

export const types = {
  SET_FILTER_STRING
}

const state = {
  topics: [],
  filterString: ''
}

function smartFilter (topics, filterString) {
  function filterValue (value, filterString) {
    return value.display_name.toLowerCase().indexOf(filterString) > -1 ||
           value.tracker.toLowerCase().indexOf(filterString) > -1
  }

  let filterStringParams = filterString.split(' ').filter(e => e).map(e => e.toLowerCase())
  return topics.filter(t => filterStringParams.every(p => filterValue(t, p)))
}

const getters = {
  filteredTopics: state => smartFilter(state.topics, state.filterString)
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
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
