import Vue from 'vue'
import Vuex from 'vuex'
import topics from './modules/topics'
import execute from './modules/execute'
import settings from './modules/settings'
import trackers from './modules/trackers'

Vue.use(Vuex)

const options = {
    state: {
        message: '',
        close: false
    },
    mutations: {
        showMessage (state, { message, close = false }) {
            state.message = message
            state.close = close
        },
        clearMessage (state) {
            state.message = ''
            state.close = false
        }
    },
    modules: {
        topics,
        execute,
        settings,
        trackers
    }
}

export default new Vuex.Store(options)
export { options }
