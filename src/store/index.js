import Vue from 'vue'
import Vuex from 'vuex'
import topics from './modules/topics'
import execute from './modules/execute'
import settings from './modules/settings'
import trackers from './modules/trackers'

Vue.use(Vuex)

const options = {
    modules: {
        topics,
        execute,
        settings,
        trackers
    }
}

export default new Vuex.Store(options)
export { options }
