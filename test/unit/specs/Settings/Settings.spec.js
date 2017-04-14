import Vue from 'vue'
import Settings from 'src/components/Settings/Settings'
import router from 'src/router'

describe('Settings.vue', function () {
    it('should render all links', async function () {
        const Constructor = Vue.extend({...Settings, router})
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.list).to.be.ok
        expect(vm.$refs.link.length).to.be.equal(7)
    })
})
