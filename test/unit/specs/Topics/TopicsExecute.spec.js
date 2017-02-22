import Vue from 'vue'
import TopicsExecute from 'src/components/Topics/TopicsExecute'
import moment from 'moment'

describe('TopicsExecute.vue', () => {
    const Constructor = Vue.extend(TopicsExecute)

    it('should display loading', async () => {
        var vm = new Constructor({ propsData: { loading: true } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.ok
        expect(vm.$refs.lastExecute).to.be.not.ok
        expect(vm.$refs.executeMenu).to.be.not.ok
    })

    it('should display last execute never', async () => {
        var vm = new Constructor({ propsData: { loading: false, execute: null } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.lastExecute).to.be.ok
        expect(vm.$refs.executeMenu).to.be.ok

        expect(vm.$refs.lastExecute.textContent).to.contain('Last Execute')
        expect(vm.$refs.lastExecute.textContent).to.contain('never')
    })

    it('should display Execute {{tracker}} menu item', async () => {
        var vm = new Constructor({ propsData: { loading: false, execute: null, trackers: ['lostfilm.tv', 'rutor.org'] } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.lastExecute).to.be.ok
        expect(vm.$refs.executeMenu).to.be.ok

        expect(vm.$refs.lastExecute.textContent).to.contain('Last Execute')
        expect(vm.$refs.lastExecute.textContent).to.contain('never')

        expect(vm.$refs.executeMenuItem).to.have.lengthOf(2)
        expect(vm.$refs.executeMenuItem[0].$el.textContent).to.contain('lostfilm.tv')
        expect(vm.$refs.executeMenuItem[1].$el.textContent).to.contain('rutor.org')
    })
})

describe('TopicsExecute.vue', () => {
    var clock

    beforeEach(() => { clock = sinon.useFakeTimers() })
    afterEach(() => clock.restore())

    const Constructor = Vue.extend(TopicsExecute)

    it('should display last execute: at 22:13 (an hour ago)', async () => {
        clock.tick(1486940625000) // 2017-02-12T23:03:45+00:00

        var vm = new Constructor({ propsData: { loading: false, execute: { finish_time: '2017-02-12T22:13:45+00:00' } } }).$mount()

        await Vue.nextTick()

        expect(vm.$refs.loading).to.be.not.ok
        expect(vm.$refs.lastExecute).to.be.ok
        expect(vm.$refs.executeMenu).to.be.ok

        expect(vm.$refs.lastExecute.textContent).to.contain('Last Execute')
        expect(vm.$refs.lastExecute.textContent).to.contain(moment('2017-02-12T22:13:45+00:00').format('HH:mm'))
        expect(vm.$refs.lastExecute.textContent).to.contain('(an hour ago)')
    })
})
